const AUTH_KEY = 'dq_auth'

export function getAuth() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_KEY) || 'null')
  } catch {
    return null
  }
}

export function saveAuth(token, user) {
  localStorage.setItem(AUTH_KEY, JSON.stringify({ token, user }))
}

export function clearAuth() {
  localStorage.removeItem(AUTH_KEY)
}

function redirectToLogin() {
  clearAuth()
  const path = window.location.pathname
  const login = path.startsWith('/farmer') ? '/farmer/login' : '/consumer/login'
  if (!path.startsWith(login)) window.location.href = login
}

async function request(path, { method = 'GET', body, formData } = {}) {
  const auth = getAuth()
  const headers = {}
  if (auth && auth.token) headers.Authorization = 'Bearer ' + auth.token
  if (body) headers['Content-Type'] = 'application/json'
  const res = await fetch(path, {
    method,
    headers,
    body: formData ? formData : body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 401) {
    redirectToLogin()
    const err = new Error('登录已过期，请重新登录')
    err.status = 401
    throw err
  }
  if (!res.ok) {
    let detail = ''
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') detail = data.detail
      else if (data.detail) detail = JSON.stringify(data.detail)
    } catch { /* ignore */ }
    const err = new Error(detail || '请求失败(' + res.status + ')')
    err.status = res.status
    throw err
  }
  if (res.status === 204) return null
  return res.json()
}

export async function login(phone, captchaCode) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: { phone, captcha_code: captchaCode },
  })
  saveAuth(data.access_token, data.user)
  return data
}

export function logout() {
  clearAuth()
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: 'POST', body }),
  upload: async (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('/api/uploads', { method: 'POST', formData: fd })
  },
}

export default api
