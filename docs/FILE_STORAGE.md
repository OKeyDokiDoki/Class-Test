# 文件存取与大文件分片

启动：`mvn -f backend/pom.xml spring-boot:run "-Dspring-boot.run.profiles=h2,files"`。
演示页：http://localhost:8080/files.html。

保留基础上传、列表和下载接口。大文件按 5 MiB 分片，后台保存每片 SHA-256 和会话，支持暂停、重试、进程重启后续传，全部到齐后按序流式合并，再校验总大小和可选的完整 SHA-256。

传输分片校验失败返回 HTTP 422、`CHUNK_CHECKSUM_MISMATCH` 和 `data.indexes`。合并发现缺片或磁盘分片损坏时，清除失效分片，返回 HTTP 409、`CHUNK_REPAIR_REQUIRED` 及需要重传的所有编号；前端只重新发送这些分片。每片最多发送三次，合并修复最多三轮；健康分片不能被不同内容覆盖。页面可勾选“故意破坏一次分片”验证真实拒收与重传，无需开放修改服务器文件的接口。

上传进度来自 `XMLHttpRequest.upload.onprogress`，结合已确认分片的实际字节数计算；传输 100% 与后台合并完成分别显示。批量上传也显示请求进度。

下载支持单范围 HTTP Range、206/416、SHA-256 强 ETag 和 If-Range。If-Range 不匹配时返回完整文件 200，客户端拒绝追加，防止拼接不同版本。

续传下载页面使用 File System Access 写入用户选择的本地文件，用 IndexedDB 保存文件句柄、偏移和 ETag。桌面 Chrome/Edge、localhost 或 HTTPS 可用；其他浏览器保留普通下载。下载逐块写入并显示实际已写入字节数。暂停或网络中断时先关闭写入流提交内容，再持久化断点；暂停后刷新可恢复。意外关闭页面只恢复最近一次已提交的断点，未提交的临时写入会丢弃。继续前检查本地文件大小和修改时间，防止向被改动的文件追加。完成后可用 Get-FileHash 比较完整 SHA-256。

数据保存在进程工作目录 `data/files`；可用 `FILE_STORAGE_ROOT` 固定绝对路径。第一阶段的 `.properties` 元数据兼容，无需迁移。合并期间建议保留约原文件三倍的磁盘空间。单个根目录由一个后端进程写入，取消会话会清理分片。

新增批量接口单次最多 100 个文件、单文件 2 MiB、总量 64 MiB，返回逐文件结果；ZIP 下载通过流输出。

下载通过 64 KiB 缓冲区流式输出，每个请求使用独立输入流，无全局下载锁。`DownloadCapacity` 用 Semaphore 控制普通、Range、ZIP 下载的总并发；`DownloadAdmissionFilter` 在 Servlet 异步完成、错误或超时时只释放一次名额。`DownloadWebConfiguration` 配置有界异步线程池与队列。默认准入 32，可用 `FILE_DOWNLOAD_CONCURRENCY` 设置 1–128；满额返回 429 和 Retry-After，线程池拒绝返回 503。`GET /api/files/download-stats` 返回当前、峰值、完成、中断/非成功响应和拒绝计数。主动暂停、错误范围与压测断开也会计入非成功计数，不能直接当作完整下载测试失败数。

正式项目保持 Spring Boot 3.3.5，Java 17 编译目标。17 项文件测试通过，正式 JAR 已启动完成 HTTP 联调；完整项目 22 项测试中有 1 项原有商户测试失败，修改前提交也可复现：`MerchantIntentApiTests.createsAndReadsMerchantIntent` 因数据库 `STATUS` 非空约束返回 500。本次未修改商户模块。录屏步骤与实测证据见 [FILE_RECORDING.md](FILE_RECORDING.md)。

默认文件上限 20 GiB，不代表已测试到该上限。此前版本曾实测 128 MiB，本次新增功能与并发验收使用 64 MiB 文件。OSS/S3 接入不在本次本地存储提交中。

测试：`mvn -f backend/pom.xml -Dtest=LocalFileApiTests,FileStorageTests test`。

HTTP 与并发验收：`python tools/file-storage/check_transfer.py --base http://localhost:8080 --out file-transfer-results`（Python 3.11+；默认上传 64 MiB、20 路完整下载，包含有意中断和超限测试）。输出目录保存测试文件及 `validation.json`，请预留磁盘空间。该目录已忽略，不提交生成文件。

实现依据：[Spring MVC 异步请求](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-async.html)、[createWritable 的提交语义](https://developer.mozilla.org/en-US/docs/Web/API/FileSystemFileHandle/createWritable)、[保存文件选择器](https://developer.mozilla.org/en-US/docs/Web/API/Window/showSaveFilePicker)。
