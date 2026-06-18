export function getSubscribeBaseUrl(): string {
  return import.meta.env.VITE_SUBSCRIBE_URL || window.location.origin
}
