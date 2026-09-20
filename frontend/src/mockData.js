export const residentData = {
  score: 82,
  label: "青年通勤型",
  district: "朝阳社区示范片区",
  dimensions: [
    { name: "生鲜购物", value: 92 },
    { name: "医疗健康", value: 68 },
    { name: "亲子教育", value: 76 },
    { name: "交通通勤", value: 89 },
    { name: "夜间服务", value: 84 }
  ],
  facilities: [
    { name: "社区生鲜店", count: 8, status: "充足" },
    { name: "社区诊所", count: 2, status: "待改善" },
    { name: "托育机构", count: 3, status: "基本满足" },
    { name: "夜间药店", count: 4, status: "充足" }
  ],
  insight: "日常购物与通勤便利，夜间医疗资源相对不足，建议关注东南侧社区卫生服务点。"
};

export const merchantData = {
  profile: "稳健型商户",
  recommendations: [
    { name: "东园路口", score: 91, demand: "高", competition: "低", rent: "6-8 万/年", type: "早餐与便利店" },
    { name: "文体中心西侧", score: 86, demand: "中高", competition: "低", rent: "8-10 万/年", type: "亲子托育" },
    { name: "康宁小区南门", score: 79, demand: "高", competition: "中", rent: "7-9 万/年", type: "药店与健康服务" }
  ]
};

export const communityData = {
  coverage: 78,
  residents: 12680,
  intents: 18,
  gaps: [
    { area: "东南片区", issue: "夜间就医距离较远", level: "高" },
    { area: "北部新居", issue: "生鲜网点承载不足", level: "中" },
    { area: "文体中心周边", issue: "托育服务供给不足", level: "中" }
  ],
  matches: [
    { merchant: "安心社区药房", area: "东南片区", fit: 94 },
    { merchant: "邻家鲜生", area: "北部新居", fit: 89 },
    { merchant: "小芽托育", area: "文体中心周边", fit: 87 }
  ]
};
