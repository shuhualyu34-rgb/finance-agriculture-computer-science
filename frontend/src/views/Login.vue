<template>
  <div class="page page-no-tab">
    <div class="logo-title">
      <div style="font-size:40px">🌾</div>
      <div class="name">{{ isFarmer ? '农户端登录' : '消费者登录' }}</div>
      <div class="slogan">{{ isFarmer ? '丹邱丝苗米普惠产融服务平台' : '溯源查询 · 田块认养' }}</div>
    </div>

    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="phone"
          label="手机号"
          type="tel"
          maxlength="11"
          placeholder="请输入手机号"
          :rules="[{ required: true, message: '请填写手机号' }]"
        />
        <van-field
          v-model="captcha"
          label="验证码"
          type="digit"
          maxlength="4"
          placeholder="请输入验证码"
        />
      </van-cell-group>
      <div style="margin: 20px 16px">
        <van-button round block type="primary" native-type="submit" :loading="loading" color="#4a7c59">
          登 录
        </van-button>
      </div>
    </van-form>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { login } from '../api'

const props = defineProps({ side: { type: String, default: 'farmer' } })
const isFarmer = props.side === 'farmer'

const router = useRouter()
const route = useRoute()
const phone = ref('')
const captcha = ref('')
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    const data = await login(phone.value, captcha.value)
    const roles = (data.user && data.user.roles) || []
    const needRole = isFarmer ? 'FARMER' : 'CONSUMER'
    if (!roles.includes(needRole)) {
      showToast(isFarmer ? '该账号不是农户账号' : '该账号不是消费者账号')
      return
    }
    showToast({ type: 'success', message: '登录成功' })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : null
    router.replace(redirect || (isFarmer ? '/farmer' : '/consumer'))
  } catch (e) {
    showToast(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>
