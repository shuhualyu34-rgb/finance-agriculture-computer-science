<template>
  <div class="page page-no-tab">
    <div class="logo-title">
      <div style="font-size:44px">🌾</div>
      <div class="name">丹邱丝苗米普惠产融服务平台</div>
      <div class="slogan">从田间到餐桌 · 溯源 · 认养 · 普惠金融</div>
    </div>
    <div class="entry-grid" style="margin-top:32px">
      <div class="entry-card" @click="$router.push('/consumer')">
        <div class="icon">🔍</div>
        <div class="name">消费端</div>
        <div class="desc">扫码溯源 / 田块认养</div>
      </div>
      <div class="entry-card" @click="$router.push('/farmer')">
        <div class="icon">👨‍🌾</div>
        <div class="name">农户端</div>
        <div class="desc">农事管理 / 认证保险贷款</div>
      </div>
    </div>
  </div>
</template>
