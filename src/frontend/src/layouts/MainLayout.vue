<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const menuItems = [
  { index: '/dashboard', label: '调度工作台' },
  { index: '/orders', label: '订单管理' },
  { index: '/goods', label: '货物管理' },
  { index: '/packages', label: '包裹管理' },
  { index: '/vehicles', label: '车辆管理' },
  { index: '/drivers', label: '司机管理' },
  { index: '/nodes/storage', label: '存储中心' },
  { index: '/nodes/sorting', label: '分拣中心' },
]

function handleLogout() {
  authStore.logout()
}
</script>

<template>
  <el-container class="layout-container">
    <el-header class="layout-header">
      <span class="layout-title">智能物流调度平台</span>
      <div class="layout-header-right">
        <span class="layout-user">{{ authStore.displayName }}</span>
        <el-button type="primary" link class="logout-button" @click="handleLogout">
          退出
        </el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" class="layout-aside">
        <el-menu :default-active="route.path" router>
          <el-menu-item
            v-for="item in menuItems"
            :key="item.index"
            :index="item.index"
          >
            {{ item.label }}
          </el-menu-item>
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
  justify-content: space-between;
  background-color: #409eff;
  color: #fff;
}

.layout-title {
  font-size: 18px;
  font-weight: 600;
}

.layout-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.layout-user {
  font-size: 14px;
}

.logout-button {
  color: #fff !important;
}

.layout-aside {
  border-right: 1px solid #e4e7ed;
}

.layout-main {
  background-color: #f5f7fa;
}
</style>
