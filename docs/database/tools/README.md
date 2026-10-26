# 数据建模工具到物理建表

本项目使用 **dbdiagram.io** 作为辅助数据建模工具：物理建表脚本不是手写的，而是由 dbdiagram.io 的 DBML（`docs/database/dbml/class_test_full.dbml`）导出生成，再执行到物理数据库中。

## 一、建模与导出链路

```text
业务需求
  └─ DBML 模型文件：docs/database/dbml/class_test_full.dbml
       ├─ 方式 A：粘贴到 https://dbdiagram.io/d，右侧可视化建模
       │          再用 Export → SQL 导出 Oracle / MySQL / PostgreSQL 脚本
       └─ 方式 B：使用 dbdiagram.io 官方 DBML CLI 导出
                  npx @dbml/cli dbml2sql class_test_full.dbml --oracle   -o schema-oracle-dbml.sql
                  npx @dbml/cli dbml2sql class_test_full.dbml --mysql    -o schema-mysql-dbml.sql
                  npx @dbml/cli dbml2sql class_test_full.dbml --postgres -o schema-postgres-dbml.sql
  └─ 物理建表：把导出的 SQL 执行到物理数据库
       ├─ Oracle 23ai：docs/database/sql/02_schema_oracle.sql（含表空间/分区版本）
       └─ H2 文件库（本机可用）：backend/src/main/resources/db/schema-dbml-h2.sql
```

## 二、本仓库中由 dbdiagram.io 导出的 SQL

| 文件 | 说明 |
| --- | --- |
| `sql/dbdiagram-export/dbml_export_oracle.sql` | dbdiagram.io DBML 引擎导出的 Oracle 方言 DDL（27 张表） |
| `sql/dbdiagram-export/dbml_export_mysql.sql` | 同上，MySQL 方言 |
| `sql/dbdiagram-export/dbml_export_postgres.sql` | 同上，PostgreSQL 方言 |
| `sql/schema-dbml-h2.sql` | 在 PostgreSQL 导出基础上仅做 H2 兼容处理（去掉 `DEFERRABLE INITIALLY IMMEDIATE`），用于 H2 文件库物理建表 |
| `backend/src/main/resources/db/schema-dbml-h2.sql` | 应用启动引导使用的同一份 H2 建表脚本 |

导出结果：27 个 `CREATE TABLE`、41 个外键、9 个复合唯一约束，字段、注释、默认值和 DBML 一致。

## 三、为什么物理库用 H2 文件库

当前开发机器上：

- Oracle 只安装了 Instant Client（`ORACLE_HOME` 指向 instantclient），没有可用的 Oracle 实例；
- MySQL / PostgreSQL / Docker 均不可用；
- 项目本身已经依赖 H2，并且 `pom.xml` 中包含 H2 驱动。

因此选择 **H2 文件库**（`jdbc:h2:file:./data/lifecircle`）作为本机可运行的物理数据库：表由 dbdiagram.io 导出的脚本创建，数据落在磁盘文件 `backend/data/lifecircle.mv.db` 中。Oracle 方言脚本保留在 `sql/02_schema_oracle.sql` 和 `sql/dbdiagram-export/dbml_export_oracle.sql`，部署到 Oracle 时直接使用。

## 四、复现步骤

```bash
# 1. 安装 Node.js 后，用官方 CLI 从 DBML 导出 DDL（或直接在 dbdiagram.io 网页导出）
npx @dbml/cli dbml2sql docs/database/dbml/class_test_full.dbml --postgres -o schema-postgres-dbml.sql

# 2. H2 兼容处理：去掉 PostgreSQL 的 DEFERRABLE INITIALLY IMMEDIATE
#    （Windows PowerShell）
(Get-Content schema-postgres-dbml.sql -Raw).Replace(' DEFERRABLE INITIALLY IMMEDIATE','') |
  Set-Content -Encoding UTF8 backend/src/main/resources/db/schema-dbml-h2.sql

# 3. 启动应用，首次启动自动用该脚本建表并写入演示数据
mvn -f backend/pom.xml spring-boot:run "-Dspring-boot.run.profiles=h2file,demo" ^
  "-Dspring-boot.run.arguments=--spring.main.web-application-type=none --persistence.exit-after-demo=true"
```

第二次用同一命令启动时，应用检测到物理表已存在，不再建表；检测到已有数据，不再写入，只输出每张表的行数，用于验证数据确实保存在磁盘上。