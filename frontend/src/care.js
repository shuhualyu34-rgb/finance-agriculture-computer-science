// 关怀模式：大字显示 + 语音播报（Web Speech API，优先粤语语音）
// 状态持久化在 localStorage，模块级 ref 全局共享，无需引入状态库
import { ref, watch } from 'vue'

const STORAGE_KEY = 'dq_care_mode'

export const careMode = ref(localStorage.getItem(STORAGE_KEY) === '1')

function applyClass(on) {
  document.documentElement.classList.toggle('care-mode', on)
}

watch(
  careMode,
  (on) => {
    localStorage.setItem(STORAGE_KEY, on ? '1' : '0')
    applyClass(on)
    if (!on) stopSpeak()
  },
  { immediate: true },
)

export function toggleCare(on) {
  careMode.value = on === undefined ? !careMode.value : !!on
}

// ===== 语音播报 =====

// 语音列表异步加载，先触发一次获取，避免首次播报拿不到语音
if ('speechSynthesis' in window) {
  window.speechSynthesis.getVoices()
}

function pickVoice() {
  const voices = window.speechSynthesis.getVoices()
  return (
    // 粤语（香港）优先，贴近本地农户语言习惯；其次普通话中文，最后任意语音
    voices.find((v) => /^yue/i.test(v.lang)) ||
    voices.find((v) => /^zh[-_]HK/i.test(v.lang)) ||
    voices.find((v) => /^zh/i.test(v.lang)) ||
    null
  )
}

export function speak(text) {
  if (!('speechSynthesis' in window)) return false
  stopSpeak()
  const utter = new SpeechSynthesisUtterance(text)
  const voice = pickVoice()
  if (voice) utter.voice = voice
  utter.lang = voice ? voice.lang : 'zh-CN'
  utter.rate = 0.9 // 稍慢语速，方便老年农户听清
  window.speechSynthesis.speak(utter)
  return true
}

export function stopSpeak() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}
