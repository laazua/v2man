import { ref } from 'vue'

export const copiedKey = ref('')

export async function copyText(text: string, key: string = text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
  copiedKey.value = key
  setTimeout(() => {
    if (copiedKey.value === key) copiedKey.value = ''
  }, 1500)
}
