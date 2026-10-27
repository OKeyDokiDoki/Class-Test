# 文件存取与大文件分片

启动：`mvn -f backend/pom.xml spring-boot:run "-Dspring-boot.run.profiles=h2,files"`。
演示页：http://localhost:8080/files.html。

保留基础上传、列表和下载接口。大文件按 5 MiB 分片，后台保存每片 SHA-256 和会话，支持暂停、重试、进程重启后续传，全部到齐后按序流式合并，再校验总大小和可选的完整 SHA-256。下载支持 HTTP Range。

数据保存在进程工作目录 `data/files`；可用 `FILE_STORAGE_ROOT` 固定绝对路径。第一阶段的 `.properties` 元数据兼容，无需迁移。合并期间建议保留约原文件三倍的磁盘空间。单个根目录由一个后端进程写入，取消会话会清理分片。

新增批量接口单次最多 100 个文件、单文件 2 MiB、总量 64 MiB，返回逐文件结果；ZIP 下载通过流输出。

独立演示环境（Spring Boot 3.5.16、Java 17 编译目标）已实测 128 MiB 文件，包括乱序分片、重复片、缺片拒绝、重启续传、合并下载 SHA-256 一致和 Range 下载。默认大小上限 20 GiB，尚未实测到该上限。正式项目仍为 Spring Boot 3.3.5，完整 Maven 联调待完成；OSS/S3 接入不在本次本地存储提交中。

测试：`mvn -f backend/pom.xml -Dtest=LocalFileApiTests,FileStorageTests test`。
