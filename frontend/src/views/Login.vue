<!--
 Notify Hub - A lightweight notification routing service.
 Copyright (C) 2025 Notify Hub Authors

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->
<script setup>
import { useRouter } from 'vue-router'
import { NotificationsOutline } from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const formRef = ref(null)
const formValue = ref({
  username: '',
  password: ''
})

const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' }
}

const API_BASE = '/api'

const handleLogin = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('username', formValue.value.username)
    formData.append('password', formValue.value.password)

    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      throw new Error('登录失败')
    }

    const data = await res.json()
    localStorage.setItem('token', data.access_token)
    message.success('欢迎回来')
    router.push('/')
  } catch (err) {
    message.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <!-- Background decoration -->
    <div class="bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <transition name="slide-up" appear>
      <div class="login-box">
        <!-- Brand -->
        <div class="brand">
          <div class="brand-icon">
            <n-icon :size="32" color="#3b82f6">
              <NotificationsOutline />
            </n-icon>
          </div>
          <h1 class="brand-title">Notify Hub</h1>
          <p class="brand-subtitle">统一消息通知中心</p>
        </div>

        <!-- Login Card -->
        <n-card :bordered="false" class="login-card">
          <n-form ref="formRef" :model="formValue" :rules="rules" size="large">
            <n-form-item path="username" label="用户名">
              <n-input
                v-model:value="formValue.username"
                placeholder="请输入用户名"
                @keyup.enter="handleLogin"
              />
            </n-form-item>
            <n-form-item path="password" label="密码">
              <n-input
                v-model:value="formValue.password"
                type="password"
                show-password-on="mousedown"
                placeholder="请输入密码"
                @keyup.enter="handleLogin"
              />
            </n-form-item>
            <n-button
              type="primary"
              block
              size="large"
              :loading="loading"
              class="login-btn"
              @click="handleLogin"
            >
              登 录
            </n-button>
          </n-form>
        </n-card>

        <div class="footer">
          Notify Hub © 2025
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0fdf4 100%);
  position: relative;
  overflow: hidden;
}

/* Background decoration circles */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.4;
}

.bg-circle-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  top: -100px;
  right: -100px;
  animation: float 8s ease-in-out infinite;
}

.bg-circle-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #10b981, #3b82f6);
  bottom: -80px;
  left: -80px;
  animation: float 10s ease-in-out infinite reverse;
}

.bg-circle-3 {
  width: 150px;
  height: 150px;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  top: 40%;
  left: 10%;
  animation: float 6s ease-in-out infinite 2s;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-20px) scale(1.05); }
}

.login-box {
  width: 100%;
  max-width: 400px;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.brand {
  text-align: center;
  margin-bottom: 32px;
}

.brand-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: white;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2);
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  color: #64748b;
  margin-top: 8px;
  font-size: 14px;
}

.login-card {
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.login-btn {
  margin-top: 8px;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
  transition: all 0.25s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

.footer {
  text-align: center;
  margin-top: 24px;
  color: #94a3b8;
  font-size: 12px;
}

/* Slide up transition */
.slide-up-enter-active {
  transition: all 0.5s ease-out;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(30px);
}

/* Mobile Responsive */
@media (max-width: 480px) {
  .login-box {
    padding: 16px;
  }
  
  .brand {
    margin-bottom: 24px;
  }
  
  .brand-icon {
    width: 56px;
    height: 56px;
  }
  
  .brand-title {
    font-size: 24px;
  }
  
  .bg-circle-1 {
    width: 200px;
    height: 200px;
    top: -50px;
    right: -50px;
  }
  
  .bg-circle-2 {
    width: 150px;
    height: 150px;
    bottom: -40px;
    left: -40px;
  }
  
  .bg-circle-3 {
    width: 80px;
    height: 80px;
  }
}
</style>
