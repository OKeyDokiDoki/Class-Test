import { nextTick, onBeforeUnmount, onMounted, watch } from "vue";
import * as echarts from "echarts";

export function useECharts(elementRef, getOption, dependencies = []) {
  let chart = null;
  let resizeObserver = null;

  async function render() {
    await nextTick();
    if (!elementRef.value) return;
    chart ??= echarts.init(elementRef.value);
    const option = getOption();
    if (option) chart.setOption(option, true);
  }

  onMounted(() => {
    render();
    if (globalThis.ResizeObserver && elementRef.value) {
      resizeObserver = new ResizeObserver(() => chart?.resize());
      resizeObserver.observe(elementRef.value);
    } else {
      globalThis.addEventListener?.("resize", resize);
    }
  });

  dependencies.forEach((dependency) => watch(dependency, render, { flush: "post" }));

  onBeforeUnmount(() => {
    resizeObserver?.disconnect();
    globalThis.removeEventListener?.("resize", resize);
    chart?.dispose();
    chart = null;
  });

  function resize() {
    chart?.resize();
  }

  return { render, resize };
}
