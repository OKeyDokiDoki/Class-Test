<script setup>
import { computed, onMounted, ref } from "vue";
import * as echarts from "echarts";
import {
  Building2, CheckCircle2, ChevronRight, CircleUserRound, MapPin,
  RefreshCw, Search, ShieldCheck, Store, UsersRound
} from "@lucide/vue";
import { getCommunityOverview, getMerchantRecommendations, getResidentAssessment } from "./api";

const activeRole = ref("resident");
const loading = ref(true);
const resident = ref(null);
const merchant = ref(null);
const community = ref(null);
const chartEl = ref(null);

const roles = [
  { id: "resident", name: "居民端", caption: "生活圈体检", icon: CircleUserRound },
  { id: "merchant", name: "商户端", caption: "智能选址", icon: Store },
  { id: "community", name: "社区端", caption: "精准招商", icon: Building2 }
];
const activeTitle = computed(() => roles.find((role) => role.id === activeRole.value)?.caption);

function renderChart() {
  if (!chartEl.value || !resident.value || activeRole.value !== "resident") return;
  const chart = echarts.init(chartEl.value);
  chart.setOption({
    radar: {
      radius: "67%", splitNumber: 4,
      axisName: { color: "#46514c", fontSize: 12 },
      splitArea: { areaStyle: { color: ["#f8faf8", "#eef3ef"] } },
      splitLine: { lineStyle: { color: "#d6dfd8" } },
      axisLine: { lineStyle: { color: "#ced8d1" } },
      indicator: resident.value.dimensions.map((item) => ({ name: item.name, max: 100 }))
    },
    series: [{
      type: "radar", symbolSize: 7,
      lineStyle: { color: "#16795a", width: 2 },
      itemStyle: { color: "#16795a" },
      areaStyle: { color: "rgba(22, 121, 90, .22)" },
      data: [{ value: resident.value.dimensions.map((item) => item.value) }]
    }]
  });
}

async function loadData() {
  loading.value = true;
  [resident.value, merchant.value, community.value] = await Promise.all([
    getResidentAssessment(), getMerchantRecommendations(), getCommunityOverview()
  ]);
  loading.value = false;
  requestAnimationFrame(renderChart);
}

function switchRole(role) {
  activeRole.value = role;
  requestAnimationFrame(renderChart);
}

onMounted(loadData);
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark"><MapPin :size="21" /></div>
        <div><strong>便民生活圈</strong><span>智能决策助手</span></div>
      </div>
      <nav aria-label="身份切换">
        <button v-for="role in roles" :key="role.id" class="role-button"
          :class="{ active: activeRole === role.id }" @click="switchRole(role.id)">
          <component :is="role.icon" :size="20" />
          <span><strong>{{ role.name }}</strong><small>{{ role.caption }}</small></span>
          <ChevronRight :size="17" />
        </button>
      </nav>
      <div class="sidebar-foot"><ShieldCheck :size="18" /><span>演示数据模式</span></div>
    </aside>

    <main>
      <header class="topbar">
        <div><p>城市 15 分钟便民生活圈</p><h1>{{ activeTitle }}</h1></div>
        <div class="top-actions">
          <label class="search"><Search :size="17" /><input aria-label="搜索小区或片区" placeholder="搜索小区或片区" /></label>
          <button class="icon-button" title="刷新数据" @click="loadData"><RefreshCw :size="18" /></button>
        </div>
      </header>

      <div v-if="loading" class="loading">正在生成生活圈分析...</div>

      <section v-else-if="activeRole === 'resident'" class="workspace">
        <div class="map-panel">
          <div class="map-toolbar">
            <div><span class="eyebrow">当前点位</span><strong>{{ resident.district }}</strong></div>
            <button class="primary-button"><MapPin :size="17" />重新选点</button>
          </div>
          <div class="mock-map">
            <div class="road road-a"></div><div class="road road-b"></div><div class="road road-c"></div>
            <div class="walk-circle"><span>15 分钟</span></div>
            <i class="poi poi-a"></i><i class="poi poi-b"></i><i class="poi poi-c"></i><i class="poi poi-d"></i>
            <div class="map-label label-a">社区卫生服务站</div>
            <div class="map-label label-b">邻里生鲜</div>
            <div class="map-label label-c">文化活动中心</div>
          </div>
          <div class="map-legend"><span><i class="dot green"></i>步行可达范围</span><span><i class="dot coral"></i>便民设施</span></div>
        </div>
        <div class="right-column">
          <div class="score-band">
            <div><span class="eyebrow">专属便利度</span><strong class="big-score">{{ resident.score }}</strong><small>/ 100</small></div>
            <div class="profile"><UsersRound :size="19" /><span>画像标签<strong>{{ resident.label }}</strong></span></div>
          </div>
          <div class="chart-panel"><div ref="chartEl" class="radar-chart"></div></div>
          <div class="insight-panel"><CheckCircle2 :size="20" /><p>{{ resident.insight }}</p></div>
        </div>
        <div class="table-panel full-width">
          <div class="section-heading"><div><span class="eyebrow">设施盘点</span><h2>步行范围内服务供给</h2></div><span>演示数据</span></div>
          <div class="facility-grid">
            <div v-for="item in resident.facilities" :key="item.name" class="facility-item">
              <span>{{ item.name }}</span><strong>{{ item.count }}</strong><small>{{ item.status }}</small>
            </div>
          </div>
        </div>
      </section>

      <section v-else-if="activeRole === 'merchant'" class="workspace merchant-workspace">
        <div class="intro-band full-width">
          <div><span class="eyebrow">商户画像</span><h2>{{ merchant.profile }}</h2><p>根据预算、经营偏好和风险承受能力推荐候选点位。</p></div>
          <button class="primary-button"><Store :size="17" />填写开店需求</button>
        </div>
        <div class="map-panel">
          <div class="map-toolbar"><div><span class="eyebrow">空间推演</span><strong>需求缺口热区</strong></div></div>
          <div class="mock-map merchant-map">
            <div class="heat heat-a"></div><div class="heat heat-b"></div><div class="heat heat-c"></div>
            <div class="road road-a"></div><div class="road road-b"></div><div class="road road-c"></div>
            <div v-for="(item, index) in merchant.recommendations" :key="item.name" class="rank-pin" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
          </div>
        </div>
        <div class="recommendation-list">
          <article v-for="(item, index) in merchant.recommendations" :key="item.name" class="recommendation">
            <div class="rank">{{ index + 1 }}</div>
            <div class="recommendation-main"><h3>{{ item.name }}</h3><p>{{ item.type }} · 租金 {{ item.rent }}</p><div><span>需求 {{ item.demand }}</span><span>竞争 {{ item.competition }}</span></div></div>
            <strong>{{ item.score }}<small> 匹配分</small></strong>
          </article>
          <button class="submit-button">提交开店意向</button>
        </div>
      </section>

      <section v-else class="workspace community-workspace">
        <div class="metrics full-width">
          <div><span>生活圈覆盖率</span><strong>{{ community.coverage }}%</strong></div>
          <div><span>辖区服务人口</span><strong>{{ community.residents.toLocaleString() }}</strong></div>
          <div><span>待对接商户</span><strong>{{ community.intents }}</strong></div>
        </div>
        <div class="table-panel">
          <div class="section-heading"><div><span class="eyebrow">问题识别</span><h2>服务短板片区</h2></div></div>
          <div v-for="gap in community.gaps" :key="gap.area" class="row-item"><div><strong>{{ gap.area }}</strong><span>{{ gap.issue }}</span></div><b :class="gap.level === '高' ? 'danger' : ''">{{ gap.level }}</b></div>
        </div>
        <div class="table-panel">
          <div class="section-heading"><div><span class="eyebrow">Agent 匹配</span><h2>优先招商建议</h2></div></div>
          <div v-for="match in community.matches" :key="match.merchant" class="row-item"><div><strong>{{ match.merchant }}</strong><span>建议对接 {{ match.area }}</span></div><b>{{ match.fit }}%</b></div>
        </div>
        <div class="simulation full-width">
          <div><span class="eyebrow">设施推演</span><h2>模拟增设便民网点</h2><p>在地图中放置网点，比较建设前后的覆盖率与受益人口。</p></div>
          <button class="primary-button"><MapPin :size="17" />开始模拟</button>
        </div>
      </section>
    </main>
  </div>
</template>
