<script setup>
import { Inbox } from "@lucide/vue";

defineProps({
  title: {
    type: String,
    default: "暂无数据"
  },
  description: {
    type: String,
    default: ""
  }
});
</script>

<template>
  <div class="base-empty" role="status">
    <Inbox :size="28" />
    <strong>{{ title }}</strong>
    <span v-if="description">{{ description }}</span>
  </div>
</template>

<style scoped>
.base-empty {
  min-height: 160px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  color: #718078;
  text-align: center;
}

.base-empty strong {
  color: #405048;
}

.base-empty span {
  font-size: 12px;
}
</style>
