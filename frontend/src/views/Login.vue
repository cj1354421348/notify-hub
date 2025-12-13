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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NCard, NInput, NButton, NForm, NFormItem, useMessage 
} from 'naive-ui'

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const formValue = ref({
  username: '',
  password: ''
})

const API_BASE = 'http://localhost:8000/api'

const handleLogin = async (e) => {
  e.preventDefault()
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
    <div class="login-box">
      <div class="login-header">
        <h1 class="app-title">Notify Hub</h1>
        <p class="app-subtitle">统一消息通知中心</p>
      </div>

      <n-card :bordered="false" size="large" class="login-card">
        <n-form @submit.prevent size="large">
          <n-form-item label="用户名">
            <n-input v-model:value="formValue.username" placeholder="请输入用户名" />
          </n-form-item>
          <n-form-item label="密码">
            <n-input v-model:value="formValue.password" type="password" show-password-on="mousedown" placeholder="请输入密码" />
          </n-form-item>
          <div class="action-bar">
            <n-button type="primary" block size="large" :loading="loading" @click="handleLogin">
              登 录
            </n-button>
          </div>
        </n-form>
      </n-card>
      
      <div class="login-footer">
        Notify Hub System © 2024
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f3f4f6;
}

.login-box {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.app-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.app-subtitle {
  color: #6b7280;
  margin-top: 8px;
  font-size: 14px;
}

.login-card {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  border-radius: 12px;
}

.action-bar {
  margin-top: 24px;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  color: #9ca3af;
  font-size: 12px;
}
</style>
