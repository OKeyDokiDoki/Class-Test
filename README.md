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
