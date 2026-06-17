import { ref } from 'vue'

const siteName = ref(import.meta.env.VITE_SITE_NAME || 'v2man')

export function useSiteName() {
  return siteName
}
