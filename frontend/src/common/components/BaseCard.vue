<script setup>
defineProps({
  as: {
    type: String,
    default: "section"
  },
  padding: {
    type: Boolean,
    default: false
  }
});
</script>

<template>
  <component :is="as" class="base-card" :class="{ 'base-card--padded': padding }">
    <slot />
  </component>
</template>

<style scoped>
.base-card {
  background: white;
  border: 1px solid #dfe6e1;
  border-radius: 8px;
}

.base-card--padded {
  padding: 19px;
}
</style>
