import { ref } from "vue";

export function useRequest(requestFn, options = {}) {
  const data = ref(options.initialData ?? null);
  const isLoading = ref(false);
  const error = ref(null);

  async function execute(...args) {
    isLoading.value = true;
    error.value = null;
    try {
      data.value = await requestFn(...args);
      return data.value;
    } catch (requestError) {
      error.value = requestError;
      if ("fallback" in options) {
        data.value =
          typeof options.fallback === "function" ? options.fallback(requestError) : options.fallback;
        return data.value;
      }
      throw requestError;
    } finally {
      isLoading.value = false;
    }
  }

  return { data, isLoading, error, execute };
}
