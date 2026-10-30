# 文件上传下载录屏：9 分 30 秒操作与讲稿

本视频包含界面演示和代码讲解，覆盖题目五项要求。建议先完整演练一次，正式视频控制在 9 分 30 秒，保留 30 秒余量。

## 录制前准备

本机已准备“录屏演示”文件夹，双击其中 `开始录屏演示.cmd`，启动完成会打开 http://localhost:8081/files.html。正式源码仍在项目 `backend/src`。演示包运行正式 Spring Boot 3.3.5 JAR，不需要再下载 Maven 依赖。

其他电脑从仓库运行：先安装 JDK 17+、Maven；在仓库根目录执行 `mvn -f backend/pom.xml -Dtest=LocalFileApiTests,FileStorageTests package`，再执行 `java -Xmx256m -jar backend/target/life-circle-backend-0.1.0.jar --spring.profiles.active=h2,files --server.port=8081`。

1. 用桌面 Chrome 或 Edge 打开演示页，勾选“演示慢速”。这是实际延迟发送/读取，让进度和暂停操作可见。
2. 准备 `测试文件/recording-large.bin`（64 MiB）、三个小文件、一个单独的下载保存文件夹。
3. 编辑器提前打开下面的源码文件，字号调大；通过函数名定位即可。也可以在 GitHub 打开相同路径阅读。
4. 试录 10 秒，检查麦克风、画面和代码是否清楚。录制范围要覆盖浏览器、代码编辑器和并发验证窗口。

## 0:00–0:25：开场

画面：展示页面和功能标题。

照着说：“我们组演示文件上传下载模块，重点包括大文件分片和损坏重传、小文件批量上传、上传下载断点续传、实时进度条，以及并发下载。先进行界面演示，再说明对应代码。”

## 0:25–1:40：大文件、损坏重传、上传断点

操作顺序：

1. 选择 64 MiB 测试文件，勾选“故意破坏一次分片”，点击“开始 / 继续上传”。
2. 向下滚到操作记录，展示 `CHUNK_CHECKSUM_MISMATCH`、重传编号和“自动重传”日志。这里只修改待发送副本的一个字节，原文件不变。
3. 点击“暂停上传”，展示已保存的大小。刷新页面，重新选择同一个原文件，继续上传。
4. 展示“后台已有 N/13 片”、进度接着增长和最终“上传完成”。完整 SHA-256 为 `a177d975313c0b0c565935d36af36baeec6348c4d78d946b5a673607761c2b60`。

照着说：“浏览器按 5 MiB 切片，每片携带编号和 SHA-256。这里故意发送损坏内容，后台计算的哈希不一致，拒收该片并返回重传编号，前端只重传这一片。暂停后，会话和正确分片仍保存在后台磁盘；刷新后选择同一个文件，前端查询已上传状态，跳过正确分片，继续传剩余部分。传输到百分之百后，后台还会校验和合并，成功后才显示上传完成。”

## 1:40–2:10：小文件批量上传

操作：多选三个小文件，点击“批量上传”，展示批量进度和三条成功结果；可勾选小文件下载 ZIP。

照着说：“小文件一次选择多个，前端放入同一个表单发送。后台逐个保存，并分别返回成功或失败结果。每批最多一百个，每个不超过两 MiB，总大小不超过六十四 MiB。”

## 2:10–3:20：下载断点与进度条

操作：

1. 对 64 MiB 文件点击“续传下载”，选择专门的下载保存位置。
2. 等进度增长后点击“暂停下载”，等到任务显示“已保存断点”。
3. 刷新页面，展示恢复的相同比例。点击“继续下载”，需要时允许写入原先选择的文件。
4. 展示日志 `HTTP 206，起始字节 …` 和最终 100%。
5. 录制前准备好文件校验命令；完成后双击演示包中的 `校验下载文件.cmd`，粘贴下载文件完整路径，展示校验通过。

照着说：“下载逐块写入本地文件，进度按实际写入字节计算。暂停时先提交写入，再保存偏移和文件句柄；所以刷新后也能恢复。继续时通过 Range 从这个字节开始请求，后台返回 206。If-Range 携带文件的 ETag，避免版本变化时把不同内容拼在一起。最后用 SHA-256 比较原文件和下载文件，确认续传后内容完整。”

补充限制：暂停并显示已保存后再刷新；意外关闭只能回到上一次已提交的断点。不要把未提交的临时写入说成已持久化。

## 3:20–3:50：并发验收演示

操作：双击演示包中的 `验证并发下载.cmd`，约数秒完成后展示 `clients: 20`、`success: 20`、`observedPeakActive: 20` 和 `allSha256Match: true`。回到网页刷新下载统计。

照着说：“这里创建二十个独立客户端同时下载完整的六十四 MiB 文件，并分别计算 SHA-256。二十份全部成功，实际观测到二十路同时下载。脚本还会故意占满名额，验证超限返回 429，断开连接后名额归零。”

统计说明：“中断 / 非成功响应”包括脚本有意断开、下载暂停和无效范围请求，不等于二十个完整下载中的失败数。统计里的峰值 32 是限流测试产生的；完整文件并发验证是 20 路。

## 3:50–5:30：讲解大文件代码

依次打开：

- [files.js](../backend/src/main/resources/static/files.js)：查找 `file.slice`、`digest`、`async function send`、`CHUNK_REPAIR_REQUIRED`。
- [ChunkUploadService.java](../backend/src/main/java/com/lifecircle/storage/ChunkUploadService.java)：查找 `init`、`chunk`、`complete`。
- [LocalFileExceptionHandler.java](../backend/src/main/java/com/lifecircle/storage/LocalFileExceptionHandler.java)：查找 `repair`。

照着说：“这里用 slice 按编号取出分片，Web Crypto 计算哈希。后台 init 保存会话，chunk 检查编号、大小和哈希；正确内容与校验文件写入磁盘。同一分片正确重试是幂等的，健康分片不能被不同内容覆盖。传输损坏返回 422 和具体编号。complete 在合并前检查全部分片；磁盘损坏或缺失时，清除失效标记，返回 409 和所有需要重传的编号。前端捕获这个结构化结果，重传相应分片后再次请求合并。合并按编号流式写入临时文件，校验总大小和可选完整哈希，再发布最终文件和元数据。失败时不会把未完成文件放入列表。”

可以展示错误结构：`{code: 'CHUNK_REPAIR_REQUIRED', data: {indexes: [1, 2], retryable: true}}`。编号从零开始；单片最多发送三次，合并修复最多三轮，持续损坏会提示错误。

## 5:30–6:05：讲解批量上传代码

打开 [files.js](../backend/src/main/resources/static/files.js) 的 `$('batch').onclick`，再打开 [LocalFileController.java](../backend/src/main/java/com/lifecircle/storage/LocalFileController.java) 的 `batch` 和 [LocalFileService.java](../backend/src/main/java/com/lifecircle/storage/LocalFileService.java) 的 `batch`。

照着说：“前端对每个文件调用 form.append，使用相同的 files 字段名。控制器通过 MultipartFile 数组接收。服务先检查数量和大小，再逐个保存。每个文件分配独立 UUID，同名文件不会互相覆盖；存储写入失败会记录在该文件的结果中。”

## 6:05–7:30：讲解上传与下载续传

打开 `files.js` 的 `localStorage`、上传状态查询和 `uploaded`；再打开 [file-downloads.js](../backend/src/main/resources/static/file-downloads.js) 的 `persisted`、`run`、`writer.close`；最后打开控制器的 `download`、`range`。

照着说：“上传端把上传编号保存在本地，后台把会话和分片保存在磁盘。继续时查询已上传编号，同时校验所选原文件的对应分片。下载端把用户选择的文件句柄、已保存字节位置和 ETag 放在 IndexedDB。下载暂停时，先关闭写入流使内容真正落盘，再保存偏移，避免记录了一个实际不存在的断点。继续前检查本地文件大小和修改时间。请求带上 Range 和 If-Range；后台定位到偏移，返回 Content-Range、Content-Length 和 206。版本不匹配返回 200，页面拒绝追加，要求重新下载。”

## 7:30–8:20：讲解进度条

打开 `files.js` 的 `xhr.upload.onprogress` 和 `progress`，以及 `file-downloads.js` 的 `current += value.byteLength`、`render`。

照着说：“上传进度等于已确认分片的字节数，加上当前分片已经发送的字节数，再除以总大小。暂停或失败时，未确认的部分会回退，以后台保存状态为准。批量上传显示整个请求的发送进度；发送完成后还需要等待后台逐个保存。下载每次写入一个数据块后增加计数，续传时从已有偏移开始计算。进度来自实际传输和写入，不使用定时器伪造增长。演示慢速只延迟实际发送或读取。”

## 8:20–9:30：讲解并发设计与实测范围

打开 [DownloadWebConfiguration.java](../backend/src/main/java/com/lifecircle/storage/DownloadWebConfiguration.java)、[DownloadCapacity.java](../backend/src/main/java/com/lifecircle/storage/DownloadCapacity.java)、[DownloadAdmissionFilter.java](../backend/src/main/java/com/lifecircle/storage/DownloadAdmissionFilter.java)，最后展示 [验收报告](validation/file-transfer.json)。

照着说：“下载使用 StreamingResponseBody 和六十四 KiB 缓冲区，每个请求独立打开输入流，不把整个文件载入内存，也没有全局串行下载锁。异步线程池与队列有明确上限，Semaphore 默认限制三十二个活跃下载。过滤器把名额保持到异步响应真正结束，在完成、异常和超时情况下都只释放一次。超出上限返回 429 和 Retry-After。我们在本机正式 Spring Boot 三点三点五项目上进行了二十路完整文件验证，全部哈希一致，同时验证了超限拒绝和连接断开后的回收。实际部署能力还受磁盘和网络带宽影响。”

结束：“以上展示了大文件与小文件的上传下载、损坏重传、双向续传、进度条和并发验证。”

## 实测与边界

- 正式 Spring Boot 3.3.5、Java 17 编译目标、JDK 26.0.2.1 运行，正式服务使用 256 MiB 堆上限。
- 文件模块 17 项测试通过；正式 HTTP 验收 9 项通过，20 份 64 MiB 并发下载全部哈希一致。
- 本机测试吞吐受磁盘缓存、本地网络和客户端读取间隔影响，不能直接作为公网吞吐承诺。默认 20 GiB 上限尚未实测到该大小。
- 全仓 22 项测试中 1 项商户模块测试失败；修改前 `b0c0880` 提交同样失败：`STATUS` 非空约束导致预期 201 实际 500。本次保留该模块，不能汇报成全仓测试全绿。
- 文件存储仍是本地磁盘，OSS/S3 和 CDN 不在本次实现范围；高并发讲解以当前代码和实测为准。
