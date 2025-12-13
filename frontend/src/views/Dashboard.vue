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

const router = useRouter()
const message = useMessage()

// State
const projects = ref([])
const messages = ref([]) // Stores the RAW full dataset
const loading = ref(true)
const selectedProjectKey = ref('all') // 'all' or project_id
const collapsed = ref(false)

// Filter State
const filterLevel = ref('all')
const searchText = ref('')
const dateRange = ref(null) // [start, end]
const loadLimit = ref(500)

const API_BASE = '/api'

// Fetchers
const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('token')
  const res = await fetch(API_BASE + url, {
    ...options,
    headers: { 
      'Authorization': `Bearer ${token}`,
      ...options.headers
    }
  })
  if (res.status === 401) {
    localStorage.removeItem('token')
    router.push('/login')
    throw new Error('Unauthorized')
  }
  return res
}

const loadData = async (isRefresh = false) => {
  if (!isRefresh && messages.value.length === 0) {
      loading.value = true
  }
  
  try {
    // Build query params for server-side slice
    let query = `?limit=${loadLimit.value}`
    if (dateRange.value) {
        // Backend expects ISO strings or compatible formats
        // ElementPlus/NaiveUI timestamps are usually ms. Convert to ISO.
        query += `&start_date=${new Date(dateRange.value[0]).toISOString()}`
        query += `&end_date=${new Date(dateRange.value[1]).toISOString()}`
    }

    const [msgRes, projRes] = await Promise.all([
      fetchWithAuth(`/messages${query}`), 
      fetchWithAuth('/projects')
    ])
    
    if (msgRes.ok) messages.value = await msgRes.json()
    if (projRes.ok) projects.value = await projRes.json()
    
    if (isRefresh) message.success('已刷新')
    
  } catch (e) {
    // console.error(e)
  } finally {
    loading.value = false
  }
}

// Handlers
// Search/Filter no longer trigger API calls -> Handled by Computed
const handleSwitchProject = (key) => {
    selectedProjectKey.value = key
    // no loadData() needed
}
const handleRefresh = () => loadData(true)

const handleDeleteMessage = async (id) => {
  try {
    const res = await fetchWithAuth(`/messages/${id}`, { method: 'DELETE' })
    if (res.ok) {
      message.success('已删除')
      loadData(false) // Silent update
    }
  } catch (e) {}
}

const handlePurge = async () => {
    try {
        const res = await fetchWithAuth(`/system/purge`, { method: 'DELETE' })
        if (res.ok) {
            const data = await res.json()
            message.success(`已清空 ${data.deleted_count} 条垃圾数据`)
            loadData(false)
        }
    } catch (e) {}
}

const handleDeleteProject = async (id, event) => {
    try {
        const res = await fetchWithAuth(`/projects/${id}`, { method: 'DELETE' })
        if (res.ok) {
            message.success('项目已删除')
            if (selectedProjectKey.value === id) selectedProjectKey.value = 'all'
            loadData(false)
        }
    } catch (e) {}
}

onMounted(() => {
  loadData(false)
})

// Client-Side Computed Filtering for Extreme Performance
const filteredMessages = computed(() => {
    let result = messages.value // Start with raw data
    
    // 1. Project Filter
    if (selectedProjectKey.value !== 'all') {
        const p = projects.value.find(x => x.id === selectedProjectKey.value)
        const pName = p ? p.name : ''
        result = result.filter(m => m.project_name === pName)
    }

    // 2. Level Filter
    if (filterLevel.value !== 'all') {
        result = result.filter(m => m.level === filterLevel.value)
    }

    // 3. Search Text
    if (searchText.value && searchText.value.trim() !== '') {
        const lowerSearch = searchText.value.toLowerCase()
        result = result.filter(m => 
            m.title.toLowerCase().includes(lowerSearch) || 
            m.content.toLowerCase().includes(lowerSearch) ||
            m.project_name.toLowerCase().includes(lowerSearch)
        )
    }
    
    return result
})

const stats = computed(() => ({
  total: filteredMessages.value.length, // Show stats based on CURRENT filter view
  errors: messages.value.filter(m => m.level === 'error').length, // Global errors always useful? Or should match filter? usually Global Errors is a dashboard key metric. Let's keep Global Errors.
  projects: projects.value.length
}))

// Menu Options Construction
const menuOptions = computed(() => {
    return [
        { 
            label: '概览', 
            key: 'overview_group', 
            type: 'group',
            children: [
               { label: '全部项目', key: 'all' }
            ]
        },
        { 
            label: '项目列表', 
            key: 'projects_group', 
            type: 'group',
            children: projects.value.map(p => ({ 
                label: p.name, 
                key: p.id
            }))
        }
    ]
})

// Table Columns
const columns = [
  { title: '级别', key: 'level', width: 90,
    render(row) {
      const typeMap = { error: 'error', warning: 'warning', success: 'success', info: 'info' }
      const textMap = { error: '错误', warning: '警告', success: '成功', info: '信息' }
      return h(NTag, { type: typeMap[row.level] || 'default', bordered: false, round: true, size: 'small' }, { default: () => textMap[row.level] || row.level.toUpperCase() })
    }
  },
  { title: '来源项目', key: 'project_name', width: 140 },
  { title: '标题', key: 'title', width: 200, ellipsis: { tooltip: true }, render(row) {
      return h('b', {}, row.title)
  }},
  { title: '内容详情', key: 'content', ellipsis: { tooltip: { width: 400 } } },
  { title: '时间', key: 'created_at', width: 170, 
    render: (row) => new Date(row.created_at).toLocaleString('zh-CN') 
  },
  { title: '操作', key: 'actions', width: 80, 
    render(row) {
      return h(
        NPopconfirm,
        {
          onPositiveClick: () => handleDeleteMessage(row.id),
          'positive-text': '确认',
          'negative-text': '取消'
        },
        {
          trigger: () => h(NButton, { size: 'tiny', type: 'error', quaternary: true }, { default: () => '删除' }),
          default: () => '确定删除这条消息吗?'
        }
      )
    }
  }
]

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<template>
  <n-layout has-sider class="layout-container">
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      class="sidebar"
    >
      <div class="logo-area">
        <span v-if="!collapsed" class="logo-text">Notify Hub</span>
        <span v-else class="logo-text-short">N</span>
      </div>
      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="selectedProjectKey"
        @update:value="handleSwitchProject"
      />
      <!-- Bottom Actions -->
      <div v-if="!collapsed" class="sidebar-footer">
        <n-popconfirm @positive-click="handlePurge">
             <template #trigger>
                <n-button block type="error" ghost size="medium">🗑️ 清空回收站</n-button>
             </template>
             确认彻底物理删除所有已标记删除的消息吗？不可恢复！
        </n-popconfirm>
      </div>
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="header">
        <div class="header-left">
          <n-breadcrumb>
            <n-breadcrumb-item>Notify Hub</n-breadcrumb-item>
            <n-breadcrumb-item>控制台</n-breadcrumb-item>
          </n-breadcrumb>
        </div>
        
        <div class="header-right">
           <div class="user-info">管理员</div>
           <n-button size="small" quaternary type="error" @click="handleLogout">
             退出登录
           </n-button>
        </div>
      </n-layout-header>

      <n-layout-content content-style="padding: 24px; background-color: #f3f4f6;">
        
        <!-- Filter Bar -->
        <n-card :bordered="true" class="mb-6 rounded-lg filter-card" size="small">
            <div class="filter-row">
                <!-- 1. Client-Side Filter: Level -->
                <div class="filter-item w-select">
                    <n-select v-model:value="filterLevel" :options="[
                        {label: '全部级别', value: 'all'},
                        {label: '信息', value: 'info'},
                        {label: '成功', value: 'success'},
                        {label: '警告', value: 'warning'},
                        {label: '错误', value: 'error'}
                    ]" size="medium" placeholder="级别" />
                </div>

                <!-- 2. Server-Side Filter: Date Range -->
                <div class="filter-item w-date">
                    <n-date-picker 
                        v-model:value="dateRange" 
                        type="datetimerange" 
                        clearable 
                        size="medium"
                        placeholder="选择时间范围"
                        @update:value="() => loadData(true)" 
                    />
                </div>

                <!-- 3. Server-Side Filter: Limit -->
                 <div class="filter-item w-limit">
                    <n-select v-model:value="loadLimit" :options="[
                        {label: '近500条', value: 500},
                        {label: '近1000条', value: 1000},
                        {label: '近2000条', value: 2000},
                        {label: '近5000条', value: 5000}
                    ]" size="medium" @update:value="() => loadData(true)" />
                </div>

                <!-- 4. Client-Side Filter: Search -->
                <div class="filter-item w-search">
                    <n-input v-model:value="searchText" placeholder="本地搜索标题或内容..." clearable>
                        <template #suffix>🔍</template>
                    </n-input>
                </div>

                <div class="spacer"></div>
                <n-button circle secondary type="primary" @click="handleRefresh" title="刷新数据">
                    <template #icon>🔄</template>
                </n-button>
            </div>
        </n-card>

        <!-- Stats Cards (Simplified) -->
        <div class="stats-grid">
           <n-card size="small" :bordered="true" class="stat-card">
              <n-statistic label="当前展示" :value="stats.total" />
           </n-card>
           <n-card size="small" :bordered="true" class="stat-card">
              <n-statistic label="异常报警" :value="stats.errors" class="text-error">
                 <template #suffix>
                    <span style="font-size: 14px; color: #d03050" v-if="stats.errors > 0">待处理</span>
                 </template>
              </n-statistic>
           </n-card>
           <n-card size="small" :bordered="true" class="stat-card">
              <n-statistic label="项目总数" :value="stats.projects" />
           </n-card>
        </div>

        <!-- Main Table -->
        <n-card title="消息列表" :bordered="true" class="main-card" size="medium">
            <template #header-extra>
                <!-- Optional: Delete Project Button if a specific project is selected -->
                 <n-popconfirm v-if="selectedProjectKey !== 'all'" @positive-click="handleDeleteProject(selectedProjectKey)">
                    <template #trigger>
                       <n-button size="small" type="error" class="mr-2">删除当前项目</n-button>
                    </template>
                    确认删除该项目吗？
                 </n-popconfirm>
            </template>
          <n-data-table
            :columns="columns"
            :data="filteredMessages"
            :loading="loading"
            :pagination="{ pageSize: 12 }"
            :max-height="'calc(100vh - 420px)'"
            :single-line="false"
            striped
          />
        </n-card>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.layout-container {
  height: 100vh;
}

.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #efeff5;
  background-color: #fff;
}

.logo-text {
  font-size: 18px;
  font-weight: bold;
  color: #2080f0;
}

.logo-text-short {
  font-size: 20px;
  font-weight: bold;
  color: #2080f0;
}

.header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background-color: #fff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  font-size: 14px;
  color: #333;
}

/* Filter Bar Styles */
.filter-card {
    background-color: #fff;
}

.filter-row {
    display: flex;
    align-items: center;
    gap: 16px;
    width: 100%;
}

.w-select {
    width: 140px;
    flex-shrink: 0;
}

.w-date {
    width: 340px;
    flex-shrink: 0;
}

.w-limit {
    width: 110px;
    flex-shrink: 0;
}

.w-search {
    width: 240px;
    flex-shrink: 0;
}

.spacer {
    flex: 1;
}

/* Stats Grid Styles */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-bottom: 24px;
}

.stat-card {
  background-color: #fff;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.main-card {
  background-color: #fff;
  border-radius: 8px;
  height: 100%;
}

.sidebar-footer {
    padding: 16px;
    display: flex;
    justify-content: center;
    border-top: 1px solid #efeff5;
    background-color: #fff;
}

:deep(.n-statistic-value__content) {
  font-weight: 600;
}
</style>
