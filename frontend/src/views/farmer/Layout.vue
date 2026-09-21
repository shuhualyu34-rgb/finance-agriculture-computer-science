<template>
  <div>
    <router-view />
    <van-tabbar route active-color="#4a7c59">
      <van-tabbar-item replace to="/farmer" icon="wap-home-o">首页</van-tabbar-item>
      <van-tabbar-item replace to="/farmer/plots" icon="chart-trending-o">田块</van-tabbar-item>
      <van-tabbar-item replace to="/farmer/upload" icon="photo-o">上传</van-tabbar-item>
      <van-tabbar-item replace to="/farmer/mine" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>
