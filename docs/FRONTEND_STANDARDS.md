# 前端开发规范

> 项目：Class-Test · 目录：`frontend/` · 文档版本：v1.2
> 本文档是 `frontend/` 开发的唯一权威约定。两名前端开发者都必须遵守；文档未覆盖、或与文档冲突的写法，一律以本文档为准。

## 目录

1. 本文档如何约束你
2. 技术栈与依赖管理
3. 目录结构与职责
4. 命名规范
5. Vue 组件规范
6. API 层与数据契约
7. 样式规范
8. 格式工具：Prettier
9. 两人协作：规则如何确定与维护
10. Git 工作流与提交规范
11. 上手清单

---

## 1. 本文档如何约束你

约束分两层，靠自觉 + 互相监督：

- **约定层**：按本文档写代码，两个人互相监督。
- **评审层**：PR 必须对方 review，违反本文档的直接打回。
- **格式**：统一用 Prettier 自动格式化（见第 8 节），不为格式争论。

想改规则：先改文档（走 PR），再改代码。禁止"先写代码后补文档"。

> 一句话：文档是约定，评审是闸门。

## 2. 技术栈与依赖管理

| 项 | 说明 |
| --- | --- |
| 编辑器 | 统一使用 **VS Code**（安装 Vue - Official 插件，带语法提示和格式化） |
| Vue 3 | ^3.5，统一使用 `<script setup>` 组合式 API |
| Vite 6 | 构建与开发服务器，端口 5173 |
| ECharts 6 | 图表（雷达图等） |
| axios | HTTP 请求 |
| @lucide/vue | 图标库 |
| Node.js | >= 20（本机 22 已验证） |
| 包管理器 | 统一 npm |

规则：

- `package-lock.json` 必须提交，装包用 `npm install`，不手动改依赖版本。
- 新增依赖前先说一声，两人都同意再装；装完跑通 `npm run dev` 和 `npm run build`。
- 不混用 pnpm / yarn，统一 npm。

## 3. 目录结构与职责

现状（脚手架）：

| 文件 | 职责 |
| --- | --- |
| `src/main.js` | 应用入口：创建实例、挂载 |
| `src/App.vue` | 三端工作台页面（居民 / 商户 / 社区） |
| `src/api.js` | 所有 HTTP 请求的唯一出口 |
| `src/mockData.js` | 演示数据（与后端字段契约一致） |
| `src/styles.css` | 全局样式与主题变量 |

扩展规则（页面变多后按此拆分）：

```text
src/
├─ components/        # 通用组件（PascalCase.vue）
├─ views/             # 页面级组件（PascalCase.vue）
├─ composables/       # 组合式函数（useXxx.js）
├─ api/               # 按域拆分的请求模块
├─ mock/              # 按域拆分的演示数据
└─ styles/            # 样式（variables.css / base.css）
```

- 一个文件只做一件事；组件超过约 300 行必须拆。
- 新文件放进对应目录，不建"杂物目录"。

## 4. 命名规范

| 对象 | 规范 | 示例 |
| --- | --- | --- |
| 组件文件 | PascalCase | `MerchantCard.vue` |
| 普通 js 文件 | camelCase | `mockData.js` |
| 组件名 | PascalCase 多词组合，避免与原生标签重名 | `MerchantCard`（不要 `Card`） |
| 变量 / 函数 | camelCase | `residentScore` |
| 布尔值 | is / has / can 前缀 | `isLoading`、`hasFacility` |
| 常量 | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT` |
| CSS 类名 | 小写 + 连字符，语义化，禁拼音禁缩写 | `map-panel`、`score-band`（沿用现状） |
| props 定义 | camelCase；模板中使用 kebab-case | `defineProps({ userName })` → `:user-name` |
| 事件名 | kebab-case | `@submit-intent` |
| API 函数 | 与后端路径一一对应 | `GET /resident/assessment` → `getResidentAssessment()` |

## 5. Vue 组件规范

- 一律 `<script setup>`，不混用 Options API。
- 块顺序：`<script setup>` → `<template>` → `<style scoped>`。
- props / emits 必须显式声明（`defineProps` / `defineEmits`），类型必填、有默认值。
- 模板内不写复杂表达式，一律进 `computed` 或函数。
- 异步数据统一模式：`loading` ref + 加载函数 + `onMounted` 触发；多接口用 `Promise.all`（沿用现有 `loadData` 写法）。
- ECharts：封装成 composable（`useECharts(elRef, option)`），统一 `init / setOption / resize / dispose`。
- 每个组件都要有加载态；演示阶段失败可回落 mock，接入真实后端后必须给用户可见的错误提示。

## 6. API 层与数据契约（本项目最重要的约定）

- 所有请求只能通过 `api.js` 的统一 axios 实例（`baseURL="/api"`、`timeout: 2500`）。
- 新增一个后端接口，必须同时完成三件事：**后端 Controller → api.js 导出函数 → mockData 字段**。mock 字段必须与后端返回完全一致（字段名、嵌套结构、类型），这是前后端联调不踩坑的根。
- `withFallback` 只允许在演示阶段使用；接入真实后端后逐个移除，改为明确的错误提示。
- 错误处理统一收敛在 `api.js`，UI 组件内不散落 try/catch。

## 7. 样式规范

- 全局变量写在 `styles.css` 的 `:root`，硬编码颜色逐步提取为变量（如 `--color-primary: #16795a`）。
- 组件内样式一律 `<style scoped>`；全局样式只能进 `styles.css`。
- 响应式断点沿用现有：`980px` / `640px`，新增断点必须注释说明。
- 新增颜色 / 间距先查变量表，不随手写死。

## 8. 格式工具：Prettier

**原理一句话**：Prettier 是代码风格的"唯一标准"——它不看你原来怎么写，一律按规则重排（引号、分号、缩进、换行），**任何代码经过它格式化后长得一样**，两人写出来的风格自动统一，不用为格式争论。

**用法**（在 `frontend/` 下）：

```bash
npm install -D prettier
npx prettier --write "src/**/*.{js,vue,css}"   # 手动格式化全部文件
```

**配合 VS Code**：安装 Prettier 插件（`esbenp.prettier-vscode`），开启保存时自动格式化：

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode"
}
```

**统一规则**：在 `frontend/` 放一份 `.prettierrc.json`（如单引号、无分号、行宽 100），两人共用同一份配置。一个工具就够，不需要其他工具链。

## 9. 两人协作：规则如何确定与维护

**确定流程（一次性）**

1. 各自写一张"最痛问题清单"（格式、命名、提交、协作各 5 条）。
2. 开一次 30 分钟对齐会：合并去重 → 逐条讨论 → 达成一致的写进本文档。
3. 文档先于代码生效。

**维护流程（长期）**

- 本文档是唯一权威。评审时发现文档没写的争议 → 当场讨论，结论先补进文档再改代码。
- 想改规则：提 PR 改文档，评审通过后生效。
- 每两周（或每个迭代）花 15 分钟回顾一次：删过时的、补新约定、版本号 +1。
- 拒绝"口头约定"：任何规则只有写进文档才算数。

## 10. Git 工作流与提交规范

- `main` 受保护，禁止直接推；开发用 `feature/xxx` 或 `fix/xxx` 分支，PR 合入，必须对方 review。
- Commit Message 格式（约定式提交，类型 + 中文描述）：

  ```text
  feat(api): 新增社区概览接口
  fix(mock): 修正商户竞争度字段
  docs(readme): 补充启动说明
  ```

  type 枚举：`feat` / `fix` / `docs` / `style` / `refactor` / `perf` / `test` / `chore`

- 提交前自检：改动已本地 `npm run dev` 验证、commit message 符合格式。

## 11. 上手清单

新接手的人：

```bash
git clone https://github.com/OKeyDokiDoki/Class-Test.git
cd frontend
npm install
npm run dev   # http://localhost:5173
```

编辑器装 VS Code + Vue - Official 插件，然后依次读：`README.md` → 本文档 → `docs/ARCHITECTURE.md`。
