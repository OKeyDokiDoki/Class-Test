# 数据库设计交付包

**项目**：城市15分钟便民生活圈与小微开店智能助手  
**版本**：V2.0　**日期**：2026年10月

## 一、文件清单

| 文件 | 说明 |
| --- | --- |
| `数据库设计说明书.docx` | 完整设计文档：数据项、数据模型、数据规划架构、表结构、存储规划、建表脚本 |
| `数据字典与数据项清单.xlsx` | 自动生成的数据项清单、表清单、字段字典、码表、索引约束、存储规划、容量汇总 |
| `dbml/class_test_full.dbml` | **dbdiagram.io 建模源文件**，复制粘贴到 https://dbdiagram.io/d 即可复现完整 ER 图 |
| `dbml/class_test_<域>.dbml` | 按主题域拆分的 DBML，便于单独查看 |
| `sql/01_tablespace_oracle.sql` | Oracle 表空间规划（DBA 执行） |
| `sql/02_schema_oracle.sql` | Oracle 23ai 生产建表脚本（27 张表） |
| `sql/03_schema_h2.sql` | H2 开发库建表脚本，已实际执行验证 |
| `sql/04_schema_mysql.sql` | MySQL 8.0 方言建表脚本（可选） |
| `sql/05_seed_data.sql` | 设施类别、画像标签、演示片区/POI 初始化数据（Oracle） |
| `sql/05_seed_data_h2.sql` | 同一份初始化数据的 H2 版本，已执行验证 |
| `sql/06_views_oracle.sql` | 社区看板视图、设施类别统计视图 |
| `sql/07_migration_v1_to_v2.sql` | 从现有 V1 `merchant_intent` 平滑升级到 V2 |
| `sql/08_validation_report.txt` | H2 建表与初始化数据验证记录 |
| `sql/09_persistence_verification.txt` | 物理建表与跨进程持久化验证记录 |
| `sql/dbdiagram-export/dbml_export_oracle.sql` | **dbdiagram.io 从 DBML 导出的 Oracle 方言 DDL**（27 张表） |
| `sql/dbdiagram-export/dbml_export_mysql.sql` | dbdiagram.io 导出的 MySQL 方言 DDL |
| `sql/dbdiagram-export/dbml_export_postgres.sql` | dbdiagram.io 导出的 PostgreSQL 方言 DDL |
| `sql/schema-dbml-h2.sql` | 由 dbdiagram.io 导出并做 H2 兼容处理的物理建表脚本 |
| `tools/README.md` | 建模工具到物理建表的完整链路与复现命令 |
| `图/` | 总体 ER、分域 ER、数据架构、数据流、存储布局图 |
| `data-model.json` | 机器可读的完整模型（供后续代码生成/校验） |

## 二、dbdiagram.io 复现步骤

1. 打开 <https://dbdiagram.io/d>。
2. 清空左侧默认示例，粘贴 `dbml/class_test_full.dbml` 的全部内容。
3. 右侧自动生成 ER 图；使用右上角 **Export → PNG/PDF** 可导出图片。
4. 表分组（TableGroup）对应六个主题域；关系线由 `Ref` 定义。
5. 修改字段时先改 DBML，再同步 `sql/` 与 Excel，保持三处一致。

## 三、建表验证

Oracle 脚本按外键依赖拓扑排序，执行顺序：

```sql
-- DBA
@01_tablespace_oracle.sql
-- 业务用户 life_circle
@02_schema_oracle.sql
@05_seed_data.sql
@06_views_oracle.sql
```

H2 开发库验证命令：

```powershell
java -cp h2-2.2.224.jar org.h2.tools.RunScript `
  -url "jdbc:h2:mem:lifecircle;MODE=Oracle;DB_CLOSE_DELAY=-1" `
  -user sa -script sql/03_schema_h2.sql
```

验证结果：27 张表、258 个字段、41 个外键全部创建成功。

## 四、物理建表与数据持久化（已落地）

物理建表**不是手写 DDL**，而是由 dbdiagram.io 从 DBML 导出，再执行到物理数据库中：

```text
docs/database/dbml/class_test_full.dbml
        │  dbdiagram.io 网页 Export → SQL
        │  或 npx @dbml/cli dbml2sql ... --postgres
        ▼
sql/dbdiagram-export/dbml_export_postgres.sql
        │  仅去掉 PostgreSQL 的 DEFERRABLE 子句以兼容 H2
        ▼
backend/src/main/resources/db/schema-dbml-h2.sql
        │  应用首次启动自动执行
        ▼
物理数据库文件 backend/data/lifecircle.mv.db（27 张表、41 个外键）
```

持久化代码位于后端：

- `backend/src/main/java/com/lifecircle/domain/*.java`：27 张表对应的 JPA 实体；
- `backend/src/main/java/com/lifecircle/repository/*Repository.java`：27 个 Spring Data JPA 仓储；
- `backend/src/main/java/com/lifecircle/config/SchemaBootstrapRunner.java`：首次启动执行 dbdiagram.io 建表脚本；
- `backend/src/main/java/com/lifecircle/service/PersistenceDemoRunner.java`：向各表写入演示数据并输出行数；
- `backend/src/main/resources/application-h2file.yml`：H2 文件库持久化配置（`ddl-auto=none`）。

运行与持久化验证：

```powershell
# 第一次：自动建表 + 写入 27 张表的演示数据
mvn -f backend/pom.xml spring-boot:run "-Dspring-boot.run.profiles=h2file,demo" `
  "-Dspring-boot.run.arguments=--spring.main.web-application-type=none --persistence.exit-after-demo=true"

# 第二次：进程重启后不写数据，只读取行数，验证数据仍在磁盘上
mvn -f backend/pom.xml spring-boot:run "-Dspring-boot.run.profiles=h2file,demo" `
  "-Dspring-boot.run.arguments=--spring.main.web-application-type=none --persistence.exit-after-demo=true"
```

实测结果：第一次启动输出 27 张表各 1 行；第二次启动输出相同行数，说明数据已持久化在 `lifecircle.mv.db` 文件中。

> 当前开发机只有 Oracle Instant Client，没有 Oracle/MySQL 实例，Docker 也不可用，因此物理库使用项目已依赖的 H2 文件库；Oracle 与 MySQL 的 dbdiagram.io 导出脚本已一并保留，部署到对应数据库时可直接执行。

## 五、设计口径

- 结构化业务数据统一放 DWD；原始接口报文保留在 ODS；评分排名等派生结果放 ADS 快照。
- 时间统一存 UTC，展示层按 Asia/Shanghai 转换。
- 手机号只存 SHA-256 哈希；商户联系方式 AES-256-GCM 加密后 Base64 存储，列表用脱敏字段。
- 枚举值中文与前端 `docs/DATA_CONVENTIONS.md` 逐字一致；英文状态码用于内部流转。
- 大表按时间分区，ODS 按月分区并压缩；索引与数据分表空间存放。
