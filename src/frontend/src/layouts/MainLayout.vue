<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Bell,
  Box,
  DocumentChecked,
  Expand,
  Fold,
  Location,
  Monitor,
  OfficeBuilding,
  SetUp,
  ShoppingCart,
  User,
  UserFilled,
  Van,
  Warning,
  TrendCharts,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const sidebarOpened = ref(true)

interface MenuItem {
  index: string
  label: string
  icon: Component
}

const menuItems: MenuItem[] = [
  { index: '/dashboard', label: '调度工作台', icon: Monitor },
  { index: '/orders', label: '订单管理', icon: ShoppingCart },
  { index: '/goods', label: '货物管理', icon: Box },
  { index: '/packages', label: '包裹管理', icon: SetUp },
  { index: '/vehicles', label: '车辆管理', icon: Van },
  { index: '/drivers', label: '司机管理', icon: User },
  { index: '/nodes/storage', label: '存储中心', icon: OfficeBuilding },
  { index: '/nodes/sorting', label: '分拣中心', icon: Location },
  { index: '/arrival-confirm', label: '节点到货确认', icon: DocumentChecked },
  { index: '/exceptions', label: '异常管理', icon: Warning },
  { index: '/notifications', label: '消息通知', icon: Bell },
  { index: '/reports', label: '报表分析', icon: TrendCharts },
]

const menuTitleMap = Object.fromEntries(menuItems.map((item) => [item.index, item.label]))

const pageTitle = computed(() => {
  const metaTitle = route.meta.title as string | undefined
  if (metaTitle) return metaTitle
  return menuTitleMap[route.path] ?? '智能物流调度平台'
})

const isCollapse = computed(() => !sidebarOpened.value)

function toggleSidebar() {
  sidebarOpened.value = !sidebarOpened.value
}

function handleLogout() {
  authStore.logout()
}
</script>

<template>
  <div
    class="app-wrapper"
    :class="{ 'hide-sidebar': isCollapse }"
  >
    <aside class="sidebar-container" :class="{ collapsed: isCollapse }">
      <div class="layout-logo">
        <span v-if="!isCollapse" class="logo-text">智能物流调度平台</span>
        <span v-else class="logo-short">物流</span>
      </div>
      <el-scrollbar class="sidebar-scroll">
        <el-menu
          :default-active="route.path"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          class="sidebar-menu"
          :background-color="'var(--layout-sidebar-bg)'"
          :text-color="'var(--layout-sidebar-text)'"
          :active-text-color="'var(--layout-sidebar-active-text)'"
        >
          <el-menu-item
            v-for="item in menuItems"
            :key="item.index"
            :index="item.index"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.label }}</template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </aside>

    <div class="main-container">
      <header class="layout-header">
        <div class="navigation-bar">
          <div class="nav-left">
            <button type="button" class="hamburger" aria-label="切换侧栏" @click="toggleSidebar">
              <el-icon :size="20">
                <Fold v-if="sidebarOpened" />
                <Expand v-else />
              </el-icon>
            </button>
            <span class="page-title">{{ pageTitle }}</span>
          </div>
          <div class="nav-right">
            <el-dropdown trigger="click">
              <div class="user-trigger">
                <el-avatar :icon="UserFilled" :size="30" />
                <span class="user-name">{{ authStore.displayName }}</span>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleLogout">
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </header>
      <main class="layout-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-wrapper {
  position: relative;
  width: 100%;
  min-height: 100vh;
}

.sidebar-container {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 2002;
  width: var(--layout-sidebar-width);
  overflow: hidden;
  background-color: var(--layout-sidebar-bg);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  transition: width 0.35s;
}

.sidebar-container.collapsed {
  width: var(--layout-sidebar-collapsed-width);
}

.layout-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  height: var(--layout-header-height);
  padding: 0 12px;
  overflow: hidden;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--layout-sidebar-active-text);
  white-space: nowrap;
}

.logo-short {
  font-size: 14px;
  font-weight: 600;
  color: var(--layout-sidebar-active-text);
}

.sidebar-scroll {
  height: calc(100vh - var(--layout-header-height));
}

.sidebar-menu {
  border-right: none;
  user-select: none;
}

.main-container {
  min-height: 100vh;
  margin-left: var(--layout-sidebar-width);
  transition: margin-left 0.35s;
}

.hide-sidebar .main-container {
  margin-left: var(--layout-sidebar-collapsed-width);
}

.layout-header {
  position: sticky;
  top: 0;
  z-index: 9;
  background-color: var(--layout-header-bg);
  box-shadow: var(--card-shadow);
  border-bottom: 1px solid var(--meta-border, #ebeef5);
}

.navigation-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--layout-header-height);
  padding: 0 16px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.hamburger {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text-primary, #303133);
  border-radius: var(--radius-sm, 4px);
}

.hamburger:hover {
  background-color: var(--meta-bg, #f5f7fa);
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #303133);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-right {
  display: flex;
  align-items: center;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm, 4px);
}

.user-trigger:hover {
  background-color: var(--meta-bg, #f5f7fa);
}

.user-name {
  font-size: 14px;
  color: var(--text-regular, #606266);
}

.layout-main {
  min-height: calc(100vh - var(--layout-header-height));
  padding: 20px;
  background-color: var(--page-bg);
  overflow-y: auto;
}

:deep(.el-menu-item) {
  position: relative;
}

:deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 2px;
  height: 100%;
  background-color: var(--el-color-primary);
}

:deep(.el-menu-item.is-active),
:deep(.el-menu-item:hover) {
  background-color: var(--layout-sidebar-hover-bg) !important;
}
</style>
