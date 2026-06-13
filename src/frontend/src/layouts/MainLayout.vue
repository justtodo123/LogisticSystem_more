<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <el-container class="layout-container">
    <el-header class="layout-header">
      <span class="layout-title">智能物流调度平台</span>
    </el-header>
    <el-container>
      <el-aside width="200px" class="layout-aside">
        <el-menu :default-active="route.path" router>
          <el-menu-item index="/health">联通测试</el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-container {
  min-height: 100vh;
}

.layout-header {
  display: flex;
  align-items: center;
  background-color: #409eff;
  color: #fff;
}

.layout-title {
  font-size: 18px;
  font-weight: 600;
}

.layout-aside {
  border-right: 1px solid #e4e7ed;
}

.layout-main {
  background-color: #f5f7fa;
}
</style>
