import { reactive } from 'vue'

const KEY = 'admin_web_auth'

function load() {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return JSON.parse(raw)
  } catch (e) { /* ignore */ }
  return null
}

export const auth = reactive({
  token: null,
  user: null,
  ...load()
})

export function setAuth(data) {
  auth.token = data.access_token
  auth.user = data.user
  localStorage.setItem(KEY, JSON.stringify({ token: auth.token, user: auth.user }))
}

export function clearAuth() {
  auth.token = null
  auth.user = null
  localStorage.removeItem(KEY)
}

export function hasRole(...roles) {
  if (!auth.user || !auth.user.roles) return false
  return roles.some((r) => auth.user.roles.includes(r))
}
