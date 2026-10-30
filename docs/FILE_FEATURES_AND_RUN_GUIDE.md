# 文件上传下载：新增功能、代码位置与运行演示

本文对照已推送的功能提交 [`21cc93b`](https://github.com/OKeyDokiDoki/Class-Test/commit/21cc93b9dbb432c1945ddb4e510e70104bb59298) 编写，说明近期文件模块的实现和复现步骤。

文件演示页面由 Spring Boot 直接提供：**启动后端，访问 `/files.html`，就能进行本次文件演示。** 页面代码位于 `backend/src/main/resources/static`；原有 Vue 业务首页是另一部分。

## 一、最近增加了什么

| 功能 | 当前行为 |
| --- | --- |
| 大文件分片上传 | 默认每片 5 MiB，后台按编号保存，全部到齐后按序流式合并。 |
| 损坏分片重传 | 传输和合并前校验 SHA-256，返回具体损坏编号，前端只重传需要修复的分片。 |
| 上传断点续传 | 浏览器保存上传编号，后台持久化会话和分片；暂停、刷新或后端重启后可继续。 |
| 小文件批量上传 | 一次选择多个文件，同一个表单提交，后台逐个保存并返回结果。 |
| 下载断点续传 | 保存本地文件句柄和已写入偏移，通过 Range、If-Range 和 HTTP 206 继续下载。 |
| 上传、下载进度条 | 根据实际发送或写入字节计算，区分“传输完成”和“后台处理完成”。 |
| 受控并发下载 | 独立输入流、64 KiB 复制缓冲、有界异步线程池、并发准入与资源回收。 |
| 批量 ZIP 下载 | 对选中的小文件流式生成 ZIP，保留独立文件名。 |
| 演示与验证 | 故意损坏一次分片的演示开关、并发统计、自动测试和真实 HTTP 验收脚本。 |

前一阶段还修正了重复的 `backend/backend/src` 目录；当前文件模块在正确的 `backend/src` 下，可以被后端正常编译。

## 二、代码从哪里看

Java 文件目录统一为 `backend/src/main/java/com/lifecircle/storage/`。

| 文件 | 职责与建议查找的位置 |
| --- | --- |
| [files.html](../backend/src/main/resources/static/files.html) | 文件选择、按钮、进度条、下载任务和统计的页面结构。 |
| [files.js](../backend/src/main/resources/static/files.js#L17) | 上传请求、切片、哈希、重试、上传续传、小文件批量和上传进度。查找 `transfer`、`send`、`uploaded`、`CHUNK_REPAIR_REQUIRED`。 |
| [file-downloads.js](../backend/src/main/resources/static/file-downloads.js#L22) | `DownloadManager` 管理下载任务；IndexedDB 保存断点；`run` 执行范围请求与本地流式写入。 |
| [LocalFileController.java](../backend/src/main/java/com/lifecircle/storage/LocalFileController.java#L14) | `/api/files` 接口入口，负责上传会话、传片、合并、批量、Range 和 ZIP 下载。 |
| [ChunkUploadService.java](../backend/src/main/java/com/lifecircle/storage/ChunkUploadService.java#L30) | `init` 建立会话，`status` 查询已上传编号，`chunk` 校验保存，`complete` 检查与合并。 |
| [ChunkRepairException.java](../backend/src/main/java/com/lifecircle/storage/ChunkRepairException.java) | 在异常中携带错误码和需要重传的分片编号。 |
| [LocalFileExceptionHandler.java](../backend/src/main/java/com/lifecircle/storage/LocalFileExceptionHandler.java#L18) | 将校验失败、需要修复、过大、参数错误和繁忙等情况转换成对应 HTTP 响应。 |
| [LocalFileService.java](../backend/src/main/java/com/lifecircle/storage/LocalFileService.java#L66) | 普通上传、元数据、列表、批量保存、SHA-256 和流式复制。查找 `publish`、`batch`、`open`。 |
| [ObjectStore.java](../backend/src/main/java/com/lifecircle/storage/ObjectStore.java) | 当前的本地磁盘适配器，负责对象写入、按偏移打开输入流、删除。 |
| [DownloadCapacity.java](../backend/src/main/java/com/lifecircle/storage/DownloadCapacity.java#L21) | Semaphore 控制活跃下载数量；Lease 保证名额只释放一次；维护并发统计。 |
| [DownloadAdmissionFilter.java](../backend/src/main/java/com/lifecircle/storage/DownloadAdmissionFilter.java#L18) | 普通、Range、ZIP 下载共享准入限制；异步完成、错误或超时后释放名额。 |
| [DownloadWebConfiguration.java](../backend/src/main/java/com/lifecircle/storage/DownloadWebConfiguration.java#L11) | 配置有界下载线程池、队列和异步超时。 |
| [application-files.yml](../backend/src/main/resources/application-files.yml) | 文件根目录、单次请求大小、异步超时和下载并发上限配置。 |

读代码可以按这个顺序：**页面 → files.js / file-downloads.js → 控制器 → 服务 → ObjectStore → 磁盘文件**。

## 三、五项重点分别如何实现

### 1. 大文件如何切片、重组，损坏后怎样重传

前端实现见 [files.js：切片与发送](../backend/src/main/resources/static/files.js#L69)，后台见 [chunk](../backend/src/main/java/com/lifecircle/storage/ChunkUploadService.java#L65) 和 [complete](../backend/src/main/java/com/lifecircle/storage/ChunkUploadService.java#L99)。

1. 前端创建上传会话，提交文件名、总大小、分片大小，以及可选的完整 SHA-256。
2. 使用 `file.slice(i * chunkSize, ...)` 按编号取片。64 MiB 文件按 5 MiB 分片时共有 13 片，最后一片 4 MiB。
3. 浏览器读取当前片并计算 SHA-256，发送会话编号、片号、片内容和哈希。编号从 **0** 开始。
4. 后台检查编号、长度，并重新计算收到内容的哈希。正确内容保存为 `i.part`，校验值保存为 `i.sha256`。
5. 合并时再次遍历磁盘分片，检查缺片、大小和哈希。失效分片会被清理，并从有效状态中移除，允许重传。
6. 后台按 `0、1、2…` 顺序流式合并到临时文件，校验最终大小和可选完整哈希，再发布最终文件与元数据。

损坏通知有两个入口：

| 情况 | 后台响应 | 前端处理 |
| --- | --- | --- |
| 收到的分片大小或哈希错误 | HTTP 422，`CHUNK_CHECKSUM_MISMATCH`，`data.indexes` 指定片号 | 重新发送该片；单次发送操作最多尝试 3 次。 |
| 合并前发现缺片或磁盘分片损坏 | HTTP 409，`CHUNK_REPAIR_REQUIRED`，列出所有待修复片号 | 仅重传列表中的分片，再请求合并；最多进行 3 轮修复。 |

例如：

```json
{
  "code": "CHUNK_REPAIR_REQUIRED",
  "message": "Missing or damaged chunks; retransmit the listed indexes",
  "data": { "indexes": [1, 2], "retryable": true }
}
```

页面的“故意破坏一次分片”开关会修改待发送副本的一个字节，同时保留原哈希，实际触发后台拒收与前端自动重传。它不会修改原文件。

### 2. 小文件如何批量上传

前端见 [files.js：批量上传](../backend/src/main/resources/static/files.js#L140)，控制器见 [batch 接口](../backend/src/main/java/com/lifecircle/storage/LocalFileController.java#L30)，保存逻辑见 [LocalFileService.batch](../backend/src/main/java/com/lifecircle/storage/LocalFileService.java#L124)。

前端对多个文件重复执行 `form.append('files', file)`，组成一个 `FormData` 请求。后台通过 `MultipartFile[]` 接收，先检查数量和大小，再逐个保存。每个文件使用独立 UUID，同名文件不会覆盖。

数量与大小限制会先统一检查；通过检查后，存储写入结果按文件分别返回。当前限制为：**每批 1–100 个，每个最多 2 MiB，总量最多 64 MiB**。

### 3. 上传和下载怎样断点续传

**上传端**：`files.js` 在 localStorage 保存上传编号，后台将会话和分片写入磁盘。继续时调用 `GET /api/files/uploads/{id}` 查询已上传片号，并核对对应分片哈希，跳过正确分片。刷新后需要重新选择同一个原文件；如果首次填写过可选完整哈希，继续时也填写同一值。

**下载端**：见 [DownloadManager.run](../backend/src/main/resources/static/file-downloads.js#L61) 和 [服务端 download](../backend/src/main/java/com/lifecircle/storage/LocalFileController.java#L43)。

- 使用 File System Access 将数据流式写入用户选择的本地文件，用 IndexedDB 保存文件句柄、偏移和 ETag。
- 暂停或网络中断时，先 `writer.close()` 提交写入，再保存偏移，避免记录不存在的断点。
- 继续前检查本地文件大小、修改时间和写入权限。
- 继续请求带上 `Range: bytes=已保存偏移-` 和 `If-Range: "文件ETag"`。
- 后台返回 HTTP 206、正确的 Content-Range 和剩余长度，页面确认后追加写入。
- If-Range 不匹配时后台返回完整文件 200，页面停止追加，要求重新下载；非法偏移返回 416。

**暂停后等待“已保存断点”再刷新**。意外关闭页面时，恢复最近一次已经提交的断点，未提交临时内容会丢弃。续传页面使用桌面 Chrome / Edge，通过 localhost 或 HTTPS 打开；其他环境可以使用普通下载。

### 4. 上传和下载进度条怎样计算

上传请求见 [transfer](../backend/src/main/resources/static/files.js#L17)，整体进度见 [progress](../backend/src/main/resources/static/files.js#L56)。

```text
上传百分比 =（后台已确认片的字节数 + 当前片已发送字节数）÷ 文件总大小 × 100%
下载百分比 =（已保存偏移 + 本次已成功写入字节数）÷ 文件总大小 × 100%
```

上传通过 `XMLHttpRequest.upload.onprogress` 获取当前请求发送比例；暂停或失败时，未确认部分会回退，以后台保存状态为准。批量上传也显示发送进度，并等待后台处理结果。

下载在 [逐块读取写入的位置](../backend/src/main/resources/static/file-downloads.js#L96) 累计 `value.byteLength`，然后更新任务进度。传输 100% 和后台合并成功是两个阶段，页面分别提示。演示慢速只是延迟真实发送或读取，没有伪造进度增长。

### 5. 怎样支持并发下载

核心代码是控制器中的 `StreamingResponseBody`、`LocalFileService.copyExactly`，以及上面三个 `Download*` 类。

| 措施 | 作用 |
| --- | --- |
| 每个请求独立输入流 | 多个下载可以同时读文件，没有全局串行下载锁。 |
| 64 KiB 复制缓冲 | 持续流式输出，避免为每个请求载入整个文件。 |
| 有界异步线程池与队列 | 对线程数量、排队数量设置上限。 |
| Semaphore 准入 | 普通下载、范围下载、ZIP 下载共享活跃请求预算，默认 32。 |
| 异步生命周期回收 | 在真正完成、错误或超时时释放名额，原子标记防止重复释放。 |
| 繁忙响应 | 准入满额返回 429 和 Retry-After；线程池拒绝返回 503。 |

目前实测的是 **20 个独立客户端同时下载完整的 64 MiB 文件，20 份全部哈希一致**。配置上限 32 与实测并发 20 是两个数值；不能据此宣称任意数量连接都能稳定下载。实际能力受磁盘、网络和服务器资源影响。

统计接口为 `GET /api/files/download-stats`。页面的“中断 / 非成功响应”包含主动暂停、无效范围和压测故意关闭连接；完整并发下载是否成功，应看验收报告中的 `success` 和 `allSha256Match`。

## 四、文件实际保存在哪里

根目录由 `FILE_STORAGE_ROOT` 指定；未设置时为后端进程工作目录下的 `data/files`。

```text
data/files/
├─ objects/                      最终文件内容，使用 UUID 命名
├─ metadata/                     文件名、大小、完整哈希、创建时间等 .properties 元数据
└─ uploads/<上传编号>/
   ├─ session.properties         上传会话
   ├─ 0.part、1.part…            分片内容
   ├─ 0.sha256、1.sha256…        每片校验记录
   └─ assembled.tmp             合并过程中的临时文件
```

合并、复制和保存期间建议预留约原文件三倍的磁盘空间。当前设计由一个后端进程写入同一个存储根目录。取消未完成会话会清理临时分片；完成后保留最终对象和元数据。

## 五、在当前电脑上最快开始演示

使用本次交付的 **“录屏演示”文件夹**：

1. 打开该文件夹，双击 `开始录屏演示.cmd`。
2. 等待出现 `READY`，浏览器会打开 `http://localhost:8081/files.html`。
3. 使用桌面 Chrome / Edge；旧页面按 Ctrl+F5 刷新。
4. 测试文件在 `测试文件` 子目录：一个 64 MiB 文件和三个小文件。
5. 结束演示时双击 `停止录屏演示.cmd`；文件数据会保留。

这个包已经包含正式 Spring Boot 3.3.5 JAR，启动时不需要再等待 Maven 下载。文件保存在包内的 `data/files`。这份本机演示包是单独交付的，不在 GitHub 源码仓库里。

## 六、从 GitHub 源码启动

### 第一步：下载并确认根目录

打开仓库首页，点击绿色 `Code` → `Download ZIP` → 解压。进入能同时看到 `backend`、`frontend`、`docs` 和 `README.md` 的目录，这就是仓库根目录。

在**文件资源管理器顶部显示文件夹路径的地址栏**输入 `powershell`，按 Enter。在弹出的窗口执行：

```powershell
Test-Path .\backend\pom.xml
```

显示 `True` 才是正确位置。如果为 `False`，先回到包含 `backend` 的那层文件夹重新打开 PowerShell。

### 第二步：检查环境

需要 JDK 17、Maven 3.9 或以上。项目编译目标为 Java 17；本次也已在 JDK 26.0.2.1 运行验证。Python 3.11+ 只用于并发验收脚本。

```powershell
java -version
mvn -version
```

两条命令应能正常显示版本，Maven 显示的 Java 路径应指向可用 JDK。当前电脑若有多个 Java 安装，可使用随本文本机说明给出的明确路径。

### 第三步：打包文件模块

在同一个根目录窗口执行：

```powershell
$env:FILE_STORAGE_ROOT = Join-Path $PWD.Path "data\files"
mvn -f .\backend\pom.xml "-Dtest=LocalFileApiTests,FileStorageTests" package
```

第一次需要下载依赖。等待出现 `BUILD SUCCESS`，生成文件为 `backend/target/life-circle-backend-0.1.0.jar`。该命令运行 17 项文件模块测试后打包；原有商户模块的单项测试问题见后文。

### 第四步：启动

继续在同一个窗口执行：

```powershell
java -Xmx256m -jar .\backend\target\life-circle-backend-0.1.0.jar "--spring.profiles.active=h2,files" --server.port=8081
```

看到 `Tomcat started on port 8081` 后，打开：

```text
http://localhost:8081/files.html
```

该源码启动方式需要保持 PowerShell 窗口开启，Ctrl+C 停止。`h2` 提供业务模块的演示数据库，`files` 加载文件上传下载配置。文件内容保存在磁盘上，与 H2 内存业务数据分开。

如果本机演示包已经占用 8081，可以直接使用它演示；如要换成自己从源码启动，先运行包内的停止脚本。也可把端口改为 8082，但浏览器和后续验收脚本的地址都要相应修改。

### 第五步：确认服务与准备文件

打开 `http://localhost:8081/api/files/config`，成功时响应 `code` 为 `"0"`，存储模式 `mode` 为 `"local"`。

已有演示包时，直接用包内测试文件。单独下载源码时，可在根目录 PowerShell 创建测试文件：

```powershell
$demoInput = Join-Path $PWD.Path "data\demo-input"
New-Item -ItemType Directory -Path $demoInput -Force | Out-Null
$demoFile = Join-Path $demoInput "sample-64MiB.bin"
if (-not (Test-Path -LiteralPath $demoFile)) {
    $demoStream = [IO.File]::Open($demoFile, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try { $demoStream.SetLength(64MB) } finally { $demoStream.Dispose() }
}
1..3 | ForEach-Object {
    "Small file $_" | Set-Content -LiteralPath (Join-Path $demoInput "small-$_.txt") -Encoding UTF8
}
```

文件位于根目录的 `data/demo-input`。该示例创建的 64 MiB 文件内容与交付包内随机测试文件不同，因此不要照抄交付包的哈希；界面的可选完整 SHA-256 留空即可。

## 七、怎样像视频一样演示

| 顺序 | 操作 | 要展示的结果 |
| --- | --- | --- |
| 1 | 勾选“演示慢速”，选择大文件，勾选“故意破坏一次分片”，开始上传。 | 进度增长；操作记录显示损坏错误码、片号和自动重传。 |
| 2 | 点击暂停，等上传按钮恢复可用；刷新页面，重新选择同一文件并继续。 | 日志显示后台已有分片，从已有进度继续，最后合并成功。 |
| 3 | 一次选择三个小文件，点击批量上传。 | 批量进度 100%，逐文件返回成功结果。 |
| 4 | 对大文件点击“续传下载”，选择保存位置；进度增长后暂停。 | 任务显示“已保存断点”和字节位置。 |
| 5 | 等断点保存后刷新，点击该任务的“继续下载”，需要时允许写入原文件。 | 进度保留；日志显示 HTTP 206 与起始字节；最终完成。 |
| 6 | 对原文件、下载文件分别执行 Get-FileHash。 | 两个完整 SHA-256 相同。 |
| 7 | 运行并发脚本，回到页面刷新统计。 | 20 份完整下载成功、哈希一致，以及资源回收结果。 |

文件校验示例，替换成自己实际的两个文件路径：

```powershell
Get-FileHash -LiteralPath "原文件完整路径" -Algorithm SHA256
Get-FileHash -LiteralPath "下载文件完整路径" -Algorithm SHA256
```

原文件和下载文件应分开放置，便于比较。上传续传继续选择原文件；下载续传继续使用已有下载任务，保留原来的部分下载文件。

并发脚本在**另一个**根目录 PowerShell 窗口执行，保留运行后端的窗口：

```powershell
python .\tools\file-storage\check_transfer.py --base http://localhost:8081 --mib 64 --concurrency 20 --out .\file-transfer-results
```

该脚本会自动生成文件、实际上传、校验损坏重传和下载续传，最后执行 20 路完整下载及超限测试。结果保存为 `file-transfer-results/validation.json`。重点看：`status: PASS`、`clients: 20`、`success: 20`、`allSha256Match: true`；峰值并发看实际输出，不使用预设结果代替。

按现有视频节奏讲解代码，可使用 [9 分 30 秒讲稿](FILE_RECORDING.md)。

## 八、常见问题

| 现象 | 处理方式 |
| --- | --- |
| PowerShell 找不到 `backend/pom.xml` | 当前层级不对；回到同时有 backend、frontend、docs 的根目录。 |
| `java` 或 `mvn` 无法运行 | 检查 JDK 和 Maven 路径；当前电脑可使用本机说明中的已验证路径。 |
| Maven 报 settings XML 格式错误 | 按错误提示定位配置；当前电脑已有隔离配置，本机说明提供 `-s`、`-gs` 的完整命令，无需修改系统文件。 |
| Maven 下载慢 | 优先使用已经交付的打包演示；源码构建第一次需要下载，缓存完成后会快很多。 |
| 8081 已被占用 | 先确认是否已有文件演示正在运行；停止自己开启的旧服务，或统一改用另一个端口。 |
| 打开的是原业务首页，没有文件按钮 | 文件演示直接进入后端 `/files.html`；浏览器地址包含正确端口和文件名。 |
| 页面没有新按钮或脚本报错 | Ctrl+F5 刷新，确认使用的是当前版本后端。 |
| 下载提示不支持保存接口 | 用桌面 Chrome / Edge 打开 localhost；普通下载仍可使用。 |
| 刷新后上传从零开始 | 重新选择同一个文件，保持相同浏览器地址；完整哈希字段也要与首次一致。 |
| 下载本地文件已修改 | 保留原断点文件；若已自行改动，移除任务后重新下载到指定位置。 |
| 不同启动方式的文件列表不同 | 对照 `FILE_STORAGE_ROOT` 和启动工作目录；演示包与源码默认不是同一个数据目录。 |
| 页面统计有中断或失败数 | 主动暂停、错误范围与压测断开也会计数；对照具体测试报告判断完整下载成功数。 |

## 九、已验证内容与当前范围

- 正式 Spring Boot 3.3.5，Java 17 编译目标；文件模块 17 项自动测试通过。
- 正式后端完成真实 HTTP 联调，20 路完整 64 MiB 下载全部 SHA-256 一致。
- 上传暂停后刷新恢复、下载暂停后刷新恢复、损坏重传及批量页面已做浏览器验证。
- [验收结果](validation/file-transfer.json) 中记录了测试范围。全仓 22 项测试中 1 项原有 `MerchantIntentApiTests` 失败：数据库 STATUS 非空约束导致预期 201、实际 500；修改前提交同样复现。文件模块测试通过，不等于整仓全部测试通过。
- 当前使用本地磁盘，OSS/S3 尚未接入。默认大文件上限 20 GiB，尚未实测到该上限；本轮新增功能与并发验收用 64 MiB，前一阶段曾实测 128 MiB。

一句话汇报：“前端按片发送并显示真实字节进度，后台校验、持久化分片并按序合并；错误返回待重传编号。上传通过会话和分片状态续传，下载通过持久化偏移、Range 和 ETag 续传；小文件使用表单数组批量处理，下载通过流式输出和有界并发控制，并以完整文件哈希验证结果。”
