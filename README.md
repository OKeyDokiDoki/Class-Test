# 城市 15 分钟便民生活圈与小微开店智能助手

面向居民、商户和社区工作人员的课程项目脚手架。项目默认使用演示数据，可以在没有高德地图 Key、Oracle 数据库和大模型 Key 的情况下先运行界面和接口。

## 项目结构

```text
.
├─ frontend/                 Vue 3 + Vite + ECharts
├─ backend/                  Spring Boot 3 REST API
├─ docs/                     项目说明与接口文档
├─ .env.example              环境变量示例
└─ docker-compose.yml        可选的 Oracle Free 数据库
```

## 最快启动

### 1. 启动前端

需要 Node.js 20 或更高版本。

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 `http://localhost:5173`。未启动后端时，前端会自动使用内置演示数据。

### 2. 启动后端

需要 Java 17 或更高版本、Maven 3.9 或更高版本。

```bash
cd backend
mvn spring-boot:run
```

接口地址为 `http://localhost:8080/api`，健康检查为 `http://localhost:8080/api/health`。

## 配置真实服务

复制 `.env.example` 为 `.env`，按需填写高德地图、大模型和 Oracle 连接信息。当前版本将地图、Agent 和数据访问封装在独立模块中，后续可以逐项替换演示实现。

### Oracle 读写分离

`oracle` Profile 下，普通事务连接主库，只读事务连接只读库：

```powershell
$env:ORACLE_MASTER_URL="jdbc:oracle:thin:@192.168.1.101:1521/FREEPDB1"
$env:ORACLE_MASTER_USERNAME="life_circle"
$env:ORACLE_MASTER_PASSWORD="life_circle"
$env:ORACLE_REPLICA_URL="jdbc:oracle:thin:@192.168.1.102:1521/FREEPDB1"
$env:ORACLE_REPLICA_USERNAME="life_circle_readonly"
$env:ORACLE_REPLICA_PASSWORD="life_circle_readonly"
mvn -f backend/pom.xml spring-boot:run "-Dspring-boot.run.profiles=oracle"
```

- `@Transactional` 写入主库。
- `@Transactional(readOnly = true)` 查询只读库。
- 未设置 `ORACLE_REPLICA_*` 时会回退到主库，便于单机开发。
- Java 配置只负责请求路由；主从复制需在数据库侧使用 Oracle Data Guard 配置。
- 从库存在复制延迟。写入后必须立即读取的数据应在同一个写事务内从主库读取。

可以使用以下接口验证持久化：

```text
POST /api/merchant/intents
GET  /api/merchant/intents
```

## 物理数据库与持久化演示

物理表由 **dbdiagram.io** 从 DBML 导出的 SQL 创建，不使用手写 DDL，也不使用 Hibernate 自动建表：

```text
docs/database/dbml/class_test_full.dbml
  → dbdiagram.io / @dbml/cli 导出 SQL
  → backend/src/main/resources/db/schema-dbml-h2.sql
  → 首次启动时由 SchemaBootstrapRunner 执行到 H2 文件库
```

`h2file` Profile 使用文件数据库 `backend/data/lifecircle.mv.db`，数据在进程重启后仍然存在：

```powershell
# 第一次：建 27 张表并写入演示数据
mvn -f backend/pom.xml spring-boot:run "-Dspring-boot.run.profiles=h2file,demo" `
  "-Dspring-boot.run.arguments=--spring.main.web-application-type=none --persistence.exit-after-demo=true"

# 第二次：进程重启后只读回行数，验证持久化
mvn -f backend/pom.xml spring-boot:run "-Dspring-boot.run.profiles=h2file,demo" `
  "-Dspring-boot.run.arguments=--spring.main.web-application-type=none --persistence.exit-after-demo=true"
```

后端已提供 27 张表的 JPA 实体与 Repository，已有 `POST/GET /api/merchant/intents` 接口也会写入同一物理库。数据库建模工具到物理建表的完整说明见 [docs/database/tools/README.md](docs/database/tools/README.md)。

## 已包含的业务骨架

- 身份选择与居民、商户画像标签。
- 居民生活圈五维评分、设施统计和诊断建议。
- 商户选址候选点、竞争度与需求缺口分析。
- 社区短板片区、招商匹配与网点模拟。
- 半月 POI 增量同步任务占位实现。
- H2 本地开发配置与 Oracle 生产配置。

详细设计见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

前端开发规范见 [docs/FRONTEND_STANDARDS.md](docs/FRONTEND_STANDARDS.md)。

公共基础层规范见 [docs/COMMON_LAYER.md](docs/COMMON_LAYER.md)。

数据项约定规范见 [docs/DATA_CONVENTIONS.md](docs/DATA_CONVENTIONS.md)。

数据库设计（数据项、dbdiagram.io 模型、数据规划架构、建表脚本与存储规划）见 [docs/database/README.md](docs/database/README.md)。
