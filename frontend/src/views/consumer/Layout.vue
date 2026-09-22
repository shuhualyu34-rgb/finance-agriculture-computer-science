<template>
  <div class="consumer-layout">
    <router-view />
    <van-tabbar route active-color="#4a7c59">
      <van-tabbar-item replace to="/consumer" icon="search">溯源</van-tabbar-item>
      <van-tabbar-item replace to="/consumer/adopt" icon="flower-o">认养</van-tabbar-item>
      <van-tabbar-item replace to="/consumer/shop" icon="shopping-cart-o">商城</van-tabbar-item>
      <van-tabbar-item replace to="/consumer/orders" icon="orders-o">订单</van-tabbar-item>
      <van-tabbar-item replace to="/consumer/mine" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>
