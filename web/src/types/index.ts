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
}

export interface Node {
  id: number
  name: string
  protocol: string
  address: string
  port: number
  config: Record<string, string>
  sort_order: number
}
