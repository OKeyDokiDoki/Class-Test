# 公共基础层规划与抽象规范

> 项目：Class-Test · 范围：`frontend/` 与 `backend/` · 文档版本：v1.0
> 本文档规定哪些代码要抽成公共基础模块/公共基础类/公共函数，放在哪里、怎么命名、怎么抽取。与 `FRONTEND_STANDARDS.md` 配合使用。

## 目录

1. 为什么要有公共层
2. 什么时候抽：抽取时机规则
3. 前端公共层（Vue 3）
4. 后端公共层（Spring Boot）
5. 依赖方向（硬规则）
6. 评审 Checklist
7. 建议落地顺序

---

## 1. 为什么要有公共层

本项目有居民 / 商户 / 社区三个端、前后端两端，白色卡片、请求加载态、评分计算这类模式会反复出现。抽成公共层后：

- 改一处，三端生效；
- 两个人不重复造轮子；
- 业务代码变薄，只写业务差异。

## 2. 什么时候抽：抽取时机规则（核心）

| 出现次数 | 做法 |
| --- | --- |
| 第 1 次 | 就地写，**不抽** |
| 第 2 次 | 立刻抽到公共层，两处都改成引用 |
| 第 3 次 | 检查公共接口设计是否合适，不合适就改公共层 |

- 只被一处使用的代码，**禁止为抽而抽**。
- 评审时发现重复代码，当场抽掉，不留第二次机会。

## 3. 前端公共层（Vue 3）

目录规划（页面变多后按此建）：

```text
src/common/
├─ components/    # 公共组件，Base 前缀命名
├─ composables/   # 公共组合式函数，useXxx 命名
├─ utils/         # 纯函数工具 + 公共算法
└─ constants/     # 常量与枚举
```

### 3.1 公共组件 `common/components/`

- 命名 `Base` 前缀：`BaseCard.vue`（现在 .map-panel / .table-panel / .chart-panel 都是同一种白色卡片）、`BaseChart.vue`（ECharts 容器）、`BaseTag.vue`、`BaseEmpty.vue`。
- 只做外观和通用交互；**业务数据一律 props 传入，组件内不许写死业务数据**。
- props / emits 显式声明，与 `FRONTEND_STANDARDS.md` 一致。

### 3.2 公共组合式函数 `common/composables/`

- `useECharts(elRef, getOption)`：封装 init / resize / dispose（现在 `App.vue` 里 renderChart 的模式抽出来）。
- `useRequest(requestFn, fallback)`：封装 loading + 请求失败回落 mock 的模式（现在 `api.js` 的 withFallback 上升为公共 composable）。

### 3.3 公共函数与算法 `common/utils/`（纯函数，最重要）

| 文件 | 放什么（结合本项目业务） |
| --- | --- |
| `format.js` | 千分位数字（人口 12,680）、分数展示、租金区间格式化 |
| `score.js` | **业务算法**：便利度五维聚合、归一化、高/中/低等级判定 |
| `geo.js` | 步行圈半径估算、坐标距离换算（接高德前先用模拟算法） |
| `validate.js` | 表单校验（开店意向提交：店名/业态/联系方式） |
| `storage.js` | localStorage 封装（记住用户上次选的居民/商户/社区身份） |

规则：utils 里的函数必须是**纯函数**——同样输入永远同样输出，不碰网络、不碰数据库、不操作 DOM。

### 3.4 常量 `common/constants/`

- `roles.js`：居民 / 商户 / 社区三端配置（现在 App.vue 里的 roles 数组）。
- 评分维度、设施类型、风险等级（高/中/低）等枚举。

## 4. 后端公共层（Spring Boot）

在 `com.lifecircle` 下新增 `common/` 包：

```text
com/lifecircle/common/
├─ result/      # 统一响应体
├─ exception/   # 异常体系
└─ utils/       # 纯静态工具类（公共算法）
```

### 4.1 公共基础类

| 类 | 作用 |
| --- | --- |
| `Result<T>` | 统一响应体：code / message / data 三段式。现在 `DemoController` 直接返回 `Map.of`，逐步迁成 `Result.ok(...)` |
| `ResultCode` 枚举 | 成功 0、参数错误 400、业务错误 BIZ_xxx、未知 500 |
| `GlobalExceptionHandler` | `@RestControllerAdvice` 全局兜底：校验失败 → 400 响应体，业务异常 → 对应 code，未知 → 500 |
| `BusinessException` | 业务错误专用异常，带 code 和 message |

### 4.2 公共算法工具类 `common/utils/`

- `CalcUtils`（静态方法）：评分计算、需求缺口、竞争度等**纯计算**——输入参数、输出结果、无副作用。
- 规则：纯计算放 utils，查库/调外部接口放 service，两层不混。

### 4.3 数据载体

- 入参 / 出参 DTO 用 Java `record`，字段带 `@NotBlank` 等校验注解（沿用 `MerchantIntent` 的写法）。

## 5. 依赖方向（硬规则）

```text
业务代码（页面 / Controller / service）  →  可以引用  common/
common/  →  禁止 import 任何业务代码
```

- `common/` 只能被别人引用，不能反过来依赖业务层，否则公共层会和业务层纠缠死。
- `utils/` 里不许出现数据库调用、HTTP 请求、DOM 操作。

## 6. 评审 Checklist

评审时逐条过：

1. 重复出现 2 次的代码，抽了没有？
2. 抽进 `common/` 的东西，有没有反向依赖业务层？
3. `utils/` 里的函数有没有副作用（网络 / 数据库 / DOM）？
4. 公共组件里有没有写死业务数据？

## 7. 建议落地顺序

1. 把 `App.vue` 的 `renderChart` 抽成 `useECharts` composable；
2. 把反复出现的白色卡片抽成 `BaseCard`；
3. 后端先建 `Result<T>` + `GlobalExceptionHandler`；
4. 评分、聚合类业务计算迁到 `score.js` / `CalcUtils`。
