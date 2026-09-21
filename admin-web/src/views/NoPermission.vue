<template>
  <el-empty description="当前账号没有管理后台访问权限">
    <el-button @click="$router.push('/login')">返回登录</el-button>
  </el-empty>
</template>
