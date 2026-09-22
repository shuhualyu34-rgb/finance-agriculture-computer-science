<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <h2>丹邱丝苗米普惠产融服务平台</h2>
      <p class="sub">管理后台登录（演示验证码：1234）</p>
      <el-form :model="form" label-width="70px">
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="请输入手机号" maxlength="11" />
        </el-form-item>
        <el-form-item label="验证码">
          <el-input v-model="form.captcha" placeholder="固定 1234" maxlength="4" @keyup.enter="doLogin" />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading" @click="doLogin">登 录</el-button>
      </el-form>
      <el-divider>演示账号（点击一键填入）</el-divider>
      <div class="demo">
        <el-button v-for="a in accounts" :key="a.phone" size="small" @click="fill(a)">
          {{ a.label }} {{ a.phone }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../api'
import { setAuth } from '../store/auth'

const router = useRouter()
const loading = ref(false)
const form = reactive({ phone: '', captcha: '1234' })

const accounts = [
  { label: '银行', phone: '13764807553' },
  { label: '农业局监管员', phone: '13731585546' },
  { label: '乡镇农技员', phone: '13754265498' },
  { label: '保险', phone: '13753091709' },
  { label: '品牌运营', phone: '13799943797' },
  { label: '管理员', phone: '13765250068' }
]

function fill(a) {
  form.phone = a.phone
  form.captcha = '1234'
}

async function doLogin() {
  if (!/^1\d{10}$/.test(form.phone)) return ElMessage.warning('请输入正确的手机号')
  loading.value = true
  try {
    const data = await http.post('/api/auth/login', { phone: form.phone, captcha_code: form.captcha })
    setAuth(data)
    ElMessage.success('登录成功')
    const roles = data.user.roles || []
    router.push(roles.includes('BANK') ? '/loans' : roles.includes('INSURANCE') ? '/policies' : roles.includes('GOVERNMENT') ? '/government' : '/certifications')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap { height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1f2d3d, #2f6f4f); }
.login-card { width: 420px; }
.sub { color: #909399; font-size: 13px; }
.demo { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
</style>
