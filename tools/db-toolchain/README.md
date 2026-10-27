# 数据库设计工具链（db-toolchain）

本目录把「顶层数据规划 → 建模工具设计 → 物理落地建表 → 开发持久化代码」四步固化成可重复执行的脚本，
原先散落在仓库外 `work/` 目录，现已纳入版本管理。

> 核心约定：**`db_model.py` 是唯一源头**。DBML、各方言 DDL、Excel 数据字典、ER 图、Word 说明书、
> JPA 实体与 Repository 全部由它派生。要改数据结构，只改 `db_model.py` 然后重新生成，不要手改产物。

---

## 一、目录结构

```
tools/db-toolchain/
├── README.md                      本文件
├── requirements.txt               Python 依赖
├── db_model.py                    ★ 唯一源头：27 张表 / 258 字段 / 6 主题域 / 码表 / 存储估算
├── gen_artifacts.py               生成 DBML、各方言 DDL、Excel 数据字典、机器可读模型
├── adapt_dialect.py               把 dbdiagram.io 导出的通用 DDL 适配成 Oracle / H2 可执行脚本
├── gen_diagrams.py                生成 PlantUML 源文件并渲染 PNG 图
├── build_design_doc.py            生成《数据库设计说明书》docx 并转 PDF（两遍编译填目录页码）
├── gen_backend_persistence.py     生成 JPA 实体、Repository、建表引导、写入校验程序
├── puml_render.py                 PlantUML 渲染小工具（puml_render.py <in.puml> <out.png>）
├── template.docx                  Word 说明书模板（build_design_doc.py 使用）
└── legacy/                        历史版本，仅作参考，不参与当前流程
    ├── build_doc.py               旧版文档生成（含硬编码绝对路径，已废弃）
    ├── make_er2.py                旧版 ER 图绘制
    ├── er.puml / er.svg / er_final.png   旧版关系图源文件与产物
```

---

## 二、端到端流程

```
① 顶层数据规划
   db_model.py（域 / 分层 / 表 / 字段 / 约束 / 索引 / 存储估算）
        │
        │  python gen_artifacts.py
        ▼
② 建模工具设计
   docs/database/dbml/*.dbml  ──粘贴──▶  dbdiagram.io  ──Export→SQL──▶  dbml_export_*.sql
        │                                                                     │
        │                                                                     │ python adapt_dialect.py
        │                                                                     ▼
        │                                          docs/database/sql/schema-dbml-oracle.sql
        │                                          backend/src/main/resources/db/schema-dbml-oracle.sql
        │                                                                     │
        │                                                                     │ 应用首次启动
        ▼                                                                     ▼
③ 物理落地建表                                              Oracle FREEPDB1 / LIFE_CIRCLE（27 张表、41 个外键）
        │
        │  python gen_backend_persistence.py
        ▼
④ 持久化代码
   backend/.../domain/*.java、repository/*Repository.java、config/*BootstrapRunner.java、service/PersistenceDemoRunner.java
```

配套产出还有：`docs/database/图/`（ER 与架构图）、`docs/database/数据库设计说明书.docx/.pdf`、
`docs/database/数据字典与数据项清单.xlsx`、`docs/database/data-model.json`。

---

## 三、脚本清单

| 脚本 | 输入 | 主要输出 | 状态 |
| --- | --- | --- | --- |
| `db_model.py` | 人工维护 | 被其它脚本 import | 维护中 |
| `gen_artifacts.py` | `db_model.py` | `dbml/*.dbml`、`sql/01..07`、`数据字典与数据项清单.xlsx`、`data-model.json`、`交付包清单.md` | 维护中 |
| `adapt_dialect.py` | dbdiagram.io 导出的 DDL | `sql/schema-dbml-{oracle,h2}.sql` + 同步到 `backend/.../resources/db/` | 维护中 |
| `gen_diagrams.py` | `db_model.py` | `puml/*.puml`、`图/*.png` | 维护中（需联网渲染） |
| `build_design_doc.py` | `db_model.py` + `图/` | `数据库设计说明书.docx` / `.pdf` | 维护中（需 LibreOffice Kit） |
| `gen_backend_persistence.py` | `db_model.py` | 27 实体 + 27 Repository + 2 个 Runner + `application-h2file.yml` | 维护中 |
| `puml_render.py` | `.puml` 文件 | `.png` | 辅助工具 |
| `legacy/*` | — | — | 已废弃，仅留档 |

`docs/database/` 下这几个文件**不由此工具链生成**，属人工维护，脚本不会覆盖：
`README.md`、`sql/schema-dbml-*.sql` 之外的补充脚本（如 `05_seed_data_h2.sql`、`08/09/10_*.txt`）、
`backend/src/main/resources/application*.yml`（除 `application-h2file.yml`）。

---

## 四、运行环境

| 依赖 | 用途 | 安装 |
| --- | --- | --- |
| Python 3.12+ | 运行全部脚本 | 系统安装 |
| openpyxl | 生成 Excel 数据字典 | `pip install -r requirements.txt` |
| python-docx | 生成 Word 说明书 | 同上 |
| pypdf | 两遍编译提取目录页码 | 同上 |
| Pillow | 图片尺寸处理 | 同上 |
| Node.js | `npx @dbml/cli` 导出 DDL | 系统安装 |
| 网络 | PlantUML 在线渲染、DBML CLI 下载 | — |
| LibreOffice Kit | docx → pdf | 可选；路径见下 |

```powershell
cd tools/db-toolchain
pip install -r requirements.txt
```

`build_design_doc.py` 需要的两个可执行文件可用环境变量覆盖，缺省值适配本机 DSH 环境：

```powershell
$env:NODE_BIN            = "C:\path\to\node.exe"
$env:LIBREOFFICE_KIT_CLI = "C:\path\to\libreoffice-kit\lib\cli.js"
```

---

## 五、按顺序执行

```powershell
cd tools/db-toolchain

# 1. 生成 DBML / DDL / 数据字典（写入仓库 docs/database/）
python gen_artifacts.py

# 2. 在 dbdiagram.io 打开 docs/database/dbml/class_test_full.dbml 校验并导出 DDL；
#    或直接用官方 CLI 导出到 docs/database/sql/dbdiagram-export/
npx @dbml/cli dbml2sql ..\..\docs\database\dbml\class_test_full.dbml --oracle   -o ..\..\docs\database\sql\dbdiagram-export\dbml_export_oracle.sql
npx @dbml/cli dbml2sql ..\..\docs\database\dbml\class_test_full.dbml --postgres -o ..\..\docs\database\sql\dbdiagram-export\dbml_export_postgres.sql

# 3. 方言适配，产出可直接执行的建表脚本（同时同步到 backend resources）
python adapt_dialect.py --target oracle
python adapt_dialect.py --target h2

# 4. 生成 ER 图与架构图
python gen_diagrams.py

# 5. 生成 Word 说明书与 PDF
python build_design_doc.py

# 6. 生成后端持久化代码
python gen_backend_persistence.py
```

第 3 步之后的物理建表有两种方式：应用首次启动时由 `OracleSchemaBootstrapRunner` 自动执行，
或由 DBA 在 `sqlplus` 中手工执行 `schema-dbml-oracle.sql`。

---

## 六、路径与环境变量

| 变量 | 作用 | 默认值 |
| --- | --- | --- |
| `DB_DESIGN_OUT` | 交付物输出目录 | `<repo>/docs/database` |
| `DB_REPO_ROOT` | 仓库根目录（供后端代码生成） | 由脚本位置向上两级推断 |
| `NODE_BIN` | node 可执行文件 | PATH 上的 `node` |
| `LIBREOFFICE_KIT_CLI` | LibreOffice Kit cli.js | DSH 自带路径 |

验证生成结果而不覆盖仓库文件：

```powershell
$env:DB_DESIGN_OUT = "$env:TEMP\design-check"
python gen_artifacts.py
```

---

## 七、常见修改场景

**新增一张表**

1. 在 `db_model.py` 中用 `table(...)` / `col(...)` 追加定义；
2. `python gen_artifacts.py` → 得到新 DBML 与 DDL；
3. `python adapt_dialect.py --target oracle` → 更新可执行建表脚本；
4. 在 dbdiagram.io 复核关系线；
5. `python gen_backend_persistence.py` → 生成新表的实体与 Repository；
6. 应用启动时若表不存在会自动补建（已存在则跳过，不会动历史数据）。

**只改字段注释或长度**：重复第 1–3 步即可。注意已上线的表 Alter 需要人工补迁移脚本（参考 `sql/07_migration_v1_to_v2.sql` 的写法）。

**换目标数据库**：导出对应方言 DDL，在 `adapt_dialect.py` 的 `ORACLE_RULES` / `H2_RULES` 旁新增一组规则即可。

---

## 八、约定与注意事项

1. **单一源头**：派生文件不要手改，否则下次生成会覆盖，且 DBML / SQL / 实体三者会不一致。
2. **禁止 ORM 自动建表**：`application.yml`（Oracle 默认）、`application-h2.yml`、`application-h2file.yml`
   都设置 `ddl-auto: none`，物理表只能来自建模工具导出的脚本。若让 Hibernate 抢建表，
   数据库默认值与 CHECK 约束会丢失（本项目曾因此触发 `ORA-01400`）。
   数据库选择由 `app.datasource.mode`（oracle/h2）决定，不依赖 profile 名称，
   因此 `-Dspring-boot.run.profiles=demo` 这类组合不会误连 Oracle。
3. **标识符大小写**：dbdiagram.io 导出的是带引号的小写标识符（`"app_user"`），
   ORM 侧必须开 `hibernate.globally_quoted_identifiers: true` 才能匹配。
4. **方言适配是必需步骤**：dbdiagram.io 的 Oracle 导出保留 `bigint` / `text` / `GENERATED AS IDENTITY`
   等通用写法，未适配前无法在 Oracle 执行。
5. **`gen_artifacts.py` 不覆盖人工 README**：它只写 `交付包清单.md`，
   `docs/database/README.md` 由人工维护。
6. **`legacy/` 里的脚本已废弃**：`build_doc.py` 含硬编码绝对路径，仅作历史参考。
7. **验证记录**：物理建表与持久化的实测结果见
   `docs/database/sql/10_oracle_persistence_verification.txt`（Oracle）与 `09_persistence_verification.txt`（H2 回退）。

---

## 九、一句话总结

```text
改 db_model.py → gen_artifacts.py → dbdiagram.io 校验并导出 → adapt_dialect.py
              → 应用首次启动自动建表 → gen_backend_persistence.py
```