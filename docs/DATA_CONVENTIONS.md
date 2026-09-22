# 数据项约定规范（DATA_CONVENTIONS）

版本：v1.0 ｜ 适用范围：前后端所有接口返回、页面展示和 mock 数据

## 1. 这份文档管什么

前后端两人开发时，最容易出问题的就是"字段对不上"。本文档是**全项目数据项的唯一权威清单**：字段叫什么、是什么类型、允许什么取值、空了怎么显示，都以这里为准。

改动顺序永远是：**先改本文档 → 再改代码**，不允许反过来。

## 2. 统一响应包裹

所有接口返回一律使用后端 `Result<T>` 包裹，前端不允许直接用裸数据：

```json
{
  "code": "0",
  "message": "成功",
  "data": { }
}
```

| code | 含义 |
| --- | --- |
| `0` | 成功 |
| `400` | 请求参数错误 |
| `BIZ_ERROR` | 业务处理失败 |
| `500` | 系统内部错误 |

前端 `api.js` 统一解包：`response.data?.data ?? response.data`——后端走包裹、mock 直出两种情况都兼容。**业务代码里不要再自己解包。**

## 3. 字段命名约定

- JSON 字段一律 **camelCase**：`score`、`beforeCoverage`、`benefitedResidents`。
- **禁止魔法值**：角色写 `ROLE_IDS.RESIDENT`，不写 `"resident"`；分数阈值读 `constants/score.js`，不写 `80`。
- 中文展示词（如"充足""待改善"）前端统一定义，后端返回值必须与之逐字一致。

## 4. 数据类型与单位约定

| 类别 | 约定 | 示例 |
| --- | --- | --- |
| 评分类 | 0–100 整数，不做字符串拼接 | `score: 82`、`fit: 94` |
| 百分比 | 0–100 整数，显示时补 `%` | `coverage: 78` |
| 数量 | 整数，展示走 `formatNumber` 千分位 | `residents: 12680` |
| 距离 | 米（m）；步行速度固定 1.2 m/s，15 分钟 ≈ 1080 m | `estimateWalkingRadius(15)` |
| 租金 | 展示字符串，单位"万/年" | `"6-8 万/年"` |
| 坐标 | `{ latitude, longitude }` 经纬度，距离用 haversine 计算 | — |
| 时间 | ISO Instant 字符串 | `/api/health` 的 `time` |

## 5. 业务数据项清单

### 5.1 居民端 `GET /api/resident/assessment`

| 字段 | 类型 | 含义 | 示例 |
| --- | --- | --- | --- |
| `score` | int | 生活圈综合评分（0–100） | 82 |
| `label` | string | 人群画像标签 | 青年通勤型 |
| `district` | string | 当前片区名 | 朝阳社区示范片区 |
| `dimensions` | array | 五维评分项 | 见下 |
| `facilities` | array | 设施盘点 | 见下 |
| `insight` | string | 诊断建议一句话 | 日常购物与通勤便利…… |

`dimensions[]`：`{ name, value }`，name 固定五项：生鲜购物、医疗健康、亲子教育、交通通勤、夜间服务；value 0–100。
`facilities[]`：`{ name, count, status }`，count 为整数，status 见第 6 节枚举。

### 5.2 商户端 `GET /api/merchant/recommendations`

| 字段 | 类型 | 含义 | 示例 |
| --- | --- | --- | --- |
| `profile` | string | 商户画像标签 | 稳健型商户 |
| `recommendations` | array | 候选点位列表 | 见下 |

`recommendations[]`：

| 字段 | 类型 | 含义 | 示例 |
| --- | --- | --- | --- |
| `name` | string | 点位名称 | 东园路口 |
| `score` | int | 选址评分（0–100） | 91 |
| `demand` | string | 需求强度，枚举见第 6 节 | 高 |
| `competition` | string | 竞争度，枚举见第 6 节 | 低 |
| `rent` | string | 租金区间 | 6-8 万/年 |
| `type` | string | 经营业态 | 早餐与便利店 |

### 5.3 商户意向 `POST /api/merchant/intents`

请求体 `MerchantIntent`：

| 字段 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- |
| `merchantName` | string | 必填 | 邻里店 |
| `businessType` | string | 必填 | 便利店 |
| `contact` | string | 必填，手机号正则 `^1[3-9]\d{9}$` | 13800138000 |

返回：`{ id, status: "submitted", merchantName }`，`id` 为毫秒时间戳。

### 5.4 社区端 `GET /api/community/overview`

| 字段 | 类型 | 含义 | 示例 |
| --- | --- | --- | --- |
| `coverage` | int | 生活圈覆盖率（%） | 78 |
| `residents` | int | 辖区服务人口 | 12680 |
| `intents` | int | 待对接意向数 | 18 |
| `gaps` | array | 短板片区 `{ area, issue, level }` | level 见枚举 |
| `matches` | array | 招商匹配 `{ merchant, area, fit }` | fit 0–100 |

### 5.5 网点模拟 `POST /api/community/simulations`

返回：`{ beforeCoverage, afterCoverage, benefitedResidents }`——覆盖率（%）与受益人口（整数）。

## 6. 枚举取值（前后端必须逐字一致）

| 枚举 | 取值 |
| --- | --- |
| 设施状态 `status` | 充足 / 基本满足 / 待改善 |
| 需求强度 `demand` | 高 / 中高 / 中 |
| 竞争度 `competition` | 低 / 中 |
| 缺口等级 `level` | 高 / 中 |
| 角色 `role` | resident / merchant / community（即 `ROLE_IDS`） |
| 分数等级 | ≥80 高 / ≥60 中 / <60 低（即 `SCORE_LEVELS`） |

## 7. 空值与展示兜底

- 数值算不出来：走 `formatNumber` / `formatScore`，显示 `--`，不显示 `null`。
- 列表为空：用 `BaseEmpty` 占位，不留空白。
- 请求失败：走 `api.js` 的 `withFallback` 回落 mock 数据。

## 8. 前后端联调硬规则

1. `frontend/src/mockData.js` 与后端返回字段必须**逐字段对齐**，本文档是对照标准。
2. 改一个字段 = 本文档 + mockData.js + 后端 + 前端，四处一起改，一次提交。
3. 已知待对齐：mockData 片区名"成都社区示范片区"与后端"朝阳社区示范片区"不一致，**以后端值为准**，下次提交时统一。

## 9. 两人协作流程

1. 谁要新增/改字段，先在本文档对应表格里补或改一行，提交说明写"已更新数据项约定"。
2. 另一人 review 文档行，确认类型、枚举、单位无误后再看代码。
3. 禁止未经本文档确认，直接在页面或接口里写新字段名。
