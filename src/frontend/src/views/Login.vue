<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import Owl from '@/components/login/Owl.vue'
import { useFocus } from '@/composables/useFocus'
import { useAuthStore } from '@/stores/auth'
import loginBg from '@/assets/login-bg.png'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { isFocus, handleBlur, handleFocus } = useFocus()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleSubmit() {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    const redirect = route.query.redirect as string | undefined
    const fallback = authStore.firstAllowedPath()
    const target = redirect && redirect !== '/login' ? redirect : fallback
    await router.push(target)
  } catch (error) {
    const message = error instanceof Error ? error.message : '登录失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page" :style="{ backgroundImage: `url(${loginBg})` }">
    <div class="login-overlay" />
    <div class="login-container">
      <Owl :close-eyes="isFocus" />
      <div class="login-card">
        <div class="login-title-block">
          <h1 class="login-title">智能物流调度平台</h1>
          <p class="login-subtitle">
            面向调度员与管理员的全链路物流可视化与智能调度演示系统
          </p>
        </div>
        <div class="login-content">
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            @submit.prevent="handleSubmit"
            @keyup.enter="handleSubmit"
          >
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名"
                type="text"
                tabindex="1"
                :prefix-icon="User"
                size="large"
                autocomplete="username"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                tabindex="2"
                :prefix-icon="Lock"
                size="large"
                show-password
                autocomplete="current-password"
                @blur="handleBlur"
                @focus="handleFocus"
                @keyup.enter="handleSubmit"
              />
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-button"
              :loading="loading"
              @click.prevent="handleSubmit"
            >
              登 录
            </el-button>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-height: 100vh;
  padding: 24px 8vw 24px 24px;
  background-color: #b8d4e8;
  background-size: cover;
  background-position: left center;
  background-repeat: no-repeat;
}

.login-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.08) 0%,
    rgba(255, 255, 255, 0.35) 55%,
    rgba(255, 255, 255, 0.72) 100%
  );
  pointer-events: none;
}

.login-container {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 440px;
}

.login-card {
  width: 100%;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow: 0 12px 40px rgba(80, 120, 160, 0.18);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px);
  overflow: hidden;
}

.login-title-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 36px 32px 8px;
  text-align: center;
}

.login-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.login-subtitle {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary, #909399);
}

.login-content {
  padding: 20px 40px 40px;
}

.login-button {
  width: 100%;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .login-page {
    justify-content: center;
    padding: 24px;
    background-position: 35% center;
  }

  .login-overlay {
    background: rgba(255, 255, 255, 0.45);
  }
}
</style>
