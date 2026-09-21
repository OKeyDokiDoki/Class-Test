# 前端开发规范

> 项目：Class-Test · 目录：`frontend/` · 文档版本：v1.0
> 本文档是 `frontend/` 开发的**唯一权威约定**。两名前端开发者都必须遵守；文档未覆盖、或与文档冲突的写法，一律以本文档为准。

## 目录

1. 本文档如何约束你
2. 技术栈与依赖管理
3. 目录结构与职责
4. 命名规范
5. Vue 组件规范
6. API 层与数据契约
7. 样式规范
8. 格式与质量工具（机器强制）
9. 两人协作：规则如何确定与维护
10. Git 工作流与提交规范
11. 上手清单
12. 附录：配置文件全文

---

## 1. 本文档如何约束你

约束分三层，缺一不可：

| 层级 | 手段 | 谁在强制 |
| --- | --- | --- |
| 约定层 | 本文档 | 团队成员互相监督 |
| 工具层 | ESLint + Prettier + husky + commitlint（提交时自动拦截） | 机器，最硬 |
| 评审层 | PR 代码评审 | 对方 |

- **写代码时**：按本文档写。
- **提交时**：工具链自动拦截不合格代码，不过关不能提交。
- **评审时**：对方按本文档逐条检查，违反即打回。
- **想改规则**：先改文档（走 PR），再改代码。禁止"先写代码后补文档"。

> 一句话：文档是约定，工具链是闸门，评审是兜底。

## 2. 技术栈与依赖管理

| 项 | 说明 |
| --- | --- |
| Vue 3 | ^3.5，统一使用 `<script setup>` 组合式 API |
| Vite 6 | 构建与开发服务器，端口 5173 |
| ECharts 6 | 图表（雷达图等） |
| axios | HTTP 请求 |
| @lucide/vue | 图标库 |
| Node.js | >= 20（本机 22 已验证） |
| 包管理器 | 统一 npm |

规则：

- `package-lock.json` 必须提交，任何人不得手动改依赖版本；装包用 `npm install`，让 lockfile 自然更新。
- 新增依赖前先说一声，两人都同意再装；装完必须跑通 `npm run dev` 和 `npm run build`。
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
├─ main.js            # 入口
├─ App.vue            # 布局 / 角色切换
├─ components/        # 通用组件（PascalCase.vue）
├─ views/             # 页面级组件（PascalCase.vue）
├─ composables/       # 组合式函数（useXxx.js）
├─ api/               # 按域拆分的请求模块（api/resident.js …）
├─ mock/              # 按域拆分的演示数据
└─ styles/            # 样式（variables.css / base.css）
```

- 单一职责：一个文件只做一件事；组件超过约 300 行必须拆。
- 新文件必须放进对应目录，不建"杂物目录"。

## 4. 命名规范

| 对象 | 规范 | 示例 |
| --- | --- | --- |
| 组件文件 | PascalCase | `MerchantCard.vue` |
| 普通 js 文件 | camelCase | `mockData.js` |
| 组件名 | PascalCase 多词组合，避免与原生标签重名 | `MerchantCard`（不要 `Card`） |
| 变量 / 函数 | camelCase | `residentScore` |
| 布尔值 | is / has / can 前缀 | `isLoading`、`hasFacility` |
| 常量 | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT` |
| CSS 类名 | 小写 + 连字符，语义化，禁拼音禁无意义缩写 | `map-panel`、`score-band`（沿用现状） |
| props 定义 | camelCase；模板中使用 kebab-case | `defineProps({ userName })` → `:user-name` |
| 事件名 | kebab-case | `@submit-intent` |
| API 函数 | 与后端路径一一对应 | `GET /resident/assessment` → `getResidentAssessment()` |

## 5. Vue 组件规范

- 一律 `<script setup>`，不混用 Options API。
- 单文件组件块顺序：`<script setup>` → `<template>` → `<style scoped>`。
- props / emits 必须显式声明（`defineProps` / `defineEmits`），类型必填、有默认值。
- 模板内不写复杂表达式，一律进 `computed` 或函数。
- 异步数据统一模式：`loading` ref + 加载函数 + `onMounted` 触发；多接口用 `Promise.all`（沿用现有 `loadData` 写法）。
- ECharts：封装成 composable（`useECharts(elRef, option)`），统一 `init / setOption / resize / dispose`；初始化前用 `requestAnimationFrame` 等 DOM 就绪（沿用现有模式）。
- 每个组件都要有加载态；演示阶段失败可静默回落 mock，接入真实后端后必须给用户可见的错误提示。

## 6. API 层与数据契约（本项目最重要的约定）

- 所有请求只能通过 `api.js` 的统一 axios 实例（`baseURL="/api"`、`timeout: 2500`）。
- 新增一个后端接口，必须同时完成三件事：**后端 Controller → api.js 导出函数 → mockData 字段**。mock 字段必须与后端返回完全一致（字段名、嵌套结构、类型），这是前后端联调不踩坑的根。
- `withFallback` 只允许在演示阶段使用；接入真实后端后逐个移除，改为明确的错误提示。
- 错误处理统一收敛在 `api.js`（interceptor / withFallback），UI 组件内不散落 try/catch。

## 7. 样式规范

- 全局变量写在 `styles.css` 的 `:root`；现有硬编码颜色逐步提取为变量：

  ```css
  :root {
    --color-primary: #16795a;
    --color-dark: #183c32;
    --color-accent: #d9f067;
    --color-danger: #a44332;
    --color-bg: #f2f5f2;
    --radius-md: 8px;
  }
  ```

- 组件内样式一律 `<style scoped>`；全局样式只能进 `styles.css`。
- 响应式断点沿用现有：`980px` / `640px`，新增断点必须注释说明。
- 新增颜色 / 间距先查变量表，不随手写死。

## 8. 格式与质量工具（机器强制）

分工：

| 工具 | 管什么 |
| --- | --- |
| EditorConfig | 缩进 2 空格、UTF-8、LF 换行 |
| Prettier | 格式统一：引号、分号、行宽 |
| ESLint | 质量与规范：未用变量、Vue 规则 |
| lint-staged | 只检查 git 暂存的文件（快） |
| husky | git 钩子：pre-commit 触发 lint-staged，commit-msg 触发 commitlint |
| commitlint | 提交信息格式 |
| GitHub Actions（可选） | 全量 lint + build 兜底 |

安装（在 `frontend/` 下执行）：

```bash
npm install -D eslint prettier @eslint/js eslint-plugin-vue @vue/eslint-config-prettier globals husky lint-staged @commitlint/cli @commitlint/config-conventional
npx husky init
```

`package.json` 增加：

```json
"scripts": {
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview",
  "lint": "eslint . --fix",
  "format": "prettier --write \"src/**/*.{js,vue,css}\"",
  "prepare": "husky"
},
"lint-staged": {
  "src/**/*.{js,vue}": ["eslint --fix", "prettier --write"],
  "src/**/*.css": ["prettier --write"]
}
```

配置文件全文见附录。装完第一步：`npm run format` 全量格式化一次，把当前不统一的代码（现有代码引号 / 分号风格不一致）一次拉齐。

## 9. 两人协作：规则如何确定与维护

**确定流程（一次性）**

1. 各自写一张"最痛问题清单"（格式、命名、提交、协作各 5 条）。
2. 开一次 30 分钟对齐会：合并去重 → 逐条讨论 → 达成一致的写进本文档。
3. 按"贴附录配置 → 全量格式化 → 提交文档"的顺序落地，**文档先于代码生效**。

**维护流程（长期）**

- 本文档是唯一权威。评审时发现文档没写的争议 → 当场讨论，结论先补进文档再改代码。
- 想改规则：提 PR 改文档，评审通过后生效，代码按新规则改。
- 每两周（或每个迭代）花 15 分钟回顾一次：删过时的、补新约定、版本号 +1。
- 拒绝"口头约定"：任何规则只有写进文档才算数。

## 10. Git 工作流与提交规范

- `main` 受保护，禁止直接推；开发用 `feature/xxx` 或 `fix/xxx` 分支，PR 合入，必须对方 review。
- Commit Message（约定式提交）：

  ```text
  feat(api): 新增社区概览接口
  fix(mock): 修正商户竞争度字段
  docs(readme): 补充启动说明
  style(workspace): 统一卡片间距
  ```

  type 枚举：`feat` / `fix` / `docs` / `style` / `refactor` / `perf` / `test` / `chore`

- 提交前自检：`npm run lint` 通过、改动已本地 `npm run dev` 验证、commit message 符合格式。

## 11. 上手清单

新接手的人：

```bash
git clone https://github.com/OKeyDokiDoki/Class-Test.git
cd frontend
npm install
npm run dev   # http://localhost:5173
```

然后依次读：`README.md` → 本文档 → `docs/ARCHITECTURE.md`。

## 12. 附录：配置文件全文

### `.editorconfig`（仓库根目录）

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
indent_style = space
indent_size = 2
insert_final_newline = true
trim_trailing_whitespace = true
```

### `.prettierrc.json`（frontend/）

```json
{
  "semi": false,
  "singleQuote": true,
  "printWidth": 100,
  "trailingComma": "none",
  "tabWidth": 2
}
```

> 说明：当前代码引号、分号风格不统一，以上是 Vite 官方模板默认风格；如果你俩更习惯分号，把 `semi` 改成 `true` 即可，但必须二选一并全量格式化一次。

### `eslint.config.js`（frontend/，ESLint 9 扁平配置）

```js
import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default [
  {
    name: 'app/files-to-lint',
    files: ['**/*.{js,mjs,jsx,vue}']
  },
  {
    name: 'app/files-to-ignore',
    ignores: ['**/dist/**', '**/dist-ssr/**', '**/coverage/**']
  },
  {
    name: 'app/globals',
    files: ['**/*.{js,mjs,jsx,vue}'],
    languageOptions: {
      globals: globals.browser
    }
  },
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  skipFormatting
]
```

### `commitlint.config.js`（frontend/）

```js
export default {
  extends: ['@commitlint/config-conventional']
}
```

### `.husky/pre-commit`

```bash
npx lint-staged
```

### `.husky/commit-msg`

```bash
npx --no -- commitlint --edit "$1"
```

### `.vscode/settings.json`（frontend/，随仓库提交，强制编辑器行为一致）

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "eslint.validate": ["javascript", "vue"]
}
```

### `.vscode/extensions.json`（frontend/，互相推荐插件）

```json
{
  "recommendations": [
    "Vue.volar",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "EditorConfig.EditorConfig"
  ]
}
```

### `.github/workflows/frontend.yml`（可选，CI 兜底）

```yaml
name: frontend-ci
on: [push, pull_request]
jobs:
  lint-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run build
```
