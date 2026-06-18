import { reactive } from 'vue'
import api from './index'

export const profile = reactive({
  username: '',
  email: '',
  balance: 0,
  is_staff: false,
  plan_name: null as string | null,
  subscription_token: null as string | null,
  traffic_used: 0,
  traffic_total: 0,
  expire_date: null as string | null,
  uuid: '',
  loaded: false,
})

export async function fetchProfile() {
  try {
    const { data } = await api.get('/auth/profile/')
    profile.username = data.username || ''
    profile.email = data.email || ''
    profile.balance = data.balance || 0
    profile.is_staff = data.is_staff || false
    profile.plan_name = data.plan_name || null
    profile.subscription_token = data.subscription_token || null
    profile.traffic_used = data.traffic_used || 0
    profile.traffic_total = data.traffic_total || 0
    profile.expire_date = data.expire_date || null
    profile.uuid = data.uuid || ''
    profile.loaded = true
  } catch {
    profile.loaded = true
  }
}
