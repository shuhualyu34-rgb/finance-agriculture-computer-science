<template>
  <div>
    <router-view />
    <van-tabbar route active-color="#4a7c59">
      <van-tabbar-item replace to="/farmer" icon="wap-home-o">首页</van-tabbar-item>
      <van-tabbar-item replace to="/farmer/plots" icon="chart-trending-o">田块</van-tabbar-item>
      <van-tabbar-item replace to="/farmer/upload" icon="photo-o">上传</van-tabbar-item>
      <van-tabbar-item replace to="/farmer/mine" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
    <div v-if="careMode" class="care-speak-btn" role="button" aria-label="朗读本页" @click="onSpeak">
      🔊<span>读屏</span>
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { careMode, speak, stopSpeak } from '../../care'

const route = useRoute()

// 换页时停止上一页的播报，避免读到旧内容
watch(() => route.fullPath, () => stopSpeak())

function onSpeak() {
  const el = document.querySelector('.page') || document.querySelector('#app')
  const text = (el ? el.innerText : '').replace(/\s+/g, ' ').trim()
  if (!text) {
    showToast('当前页面没有可读内容')
    return
  }
  if (!speak(text)) showToast('当前浏览器不支持语音播报')
}
</script>
