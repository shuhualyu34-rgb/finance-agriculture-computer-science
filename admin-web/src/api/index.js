import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'
import { auth, clearAuth } from '../store/auth'

const http = axios.create({ baseURL: '', timeout: 20000 })

http.interceptors.request.use((config) => {
  if (auth.token) config.headers.Authorization = 'Bearer ' + auth.token
  return config
})

http.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    const status = err.response && err.response.status
    const detail = err.response && err.response.data && err.response.data.detail
    const msg = typeof detail === 'string' ? detail : (err.message || '请求失败')
    if (status === 401) {
      clearAuth()
      ElMessage.error('登录已失效，请重新登录')
      router.push('/login')
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  }
)

export default http
