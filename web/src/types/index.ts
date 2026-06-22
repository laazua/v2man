export interface User {
  id: number
  username: string
  email: string
  uuid: string
  plan_name: string | null
  traffic_used: number
  traffic_total: number
  expire_date: string | null
  date_joined: string
  is_staff: boolean
  balance: number
  subscription_token: string | null
  is_active: boolean
}

export interface Node {
  id: number
  name: string
  protocol: string
  address: string
  port: number
  config: Record<string, string>
  config_path: string
  reload_cmd: string
  sort_order: number
  is_active: boolean
  ssh_host: string
  ssh_port: number
  ssh_user: string
  ssh_configured: boolean
  deployed_at: string | null
}

export interface Plan {
  id: number
  name: string
  price_display: string
  traffic_limit: number
  duration_days: number
  is_active: boolean
}
