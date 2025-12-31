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
import { NTag, NButton, NPopconfirm, NIcon, NDropdown } from 'naive-ui'
import {
  HomeOutline,
  FolderOutline,
  NotificationsOutline,
  AlertCircleOutline,
  EllipsisVertical,
  TrashOutline,
  RefreshOutline,
  CopyOutline,
  FilterOutline,
  MenuOutline
} from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()

// State
const projects = ref([])
const messages = ref([])
const loading = ref(true)
const selectedProjectKey = ref('all')
const checkedRowKeys = ref([])

// Filter State
const filterLevel = ref('all')
const searchText = ref('')
const dateRange = ref(null)
const loadLimit = ref(500)
const showFilterDrawer = ref(false)

// Responsive
const isMobile = ref(false)
const collapsed = ref(true)
const showMobileSidebar = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) {
    collapsed.value = true
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadData(false)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

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
    throw new Error('会话已过期，请重新登录')
  }
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || `请求失败 (${res.status})`)
  }
  return res
}

const loadData = async (isRefresh = false) => {
  if (!isRefresh && messages.value.length === 0) {
    loading.value = true
  }

  try {
    let query = `?limit=${loadLimit.value}`
    if (dateRange.value) {
      query += `&start_date=${new Date(dateRange.value[0]).toISOString()}`
      query += `&end_date=${new Date(dateRange.value[1]).toISOString()}`
    }

    const [msgRes, projRes] = await Promise.all([
      fetchWithAuth(`/messages${query}`),
      fetchWithAuth('/projects')
    ])

    messages.value = await msgRes.json()
    projects.value = await projRes.json()

    if (isRefresh) message.success('已刷新')
  } catch (e) {
    message.error(e.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// Handlers
const handleSwitchProject = (key) => {
  selectedProjectKey.value = key
}

const handleMobileSwitchProject = (key) => {
  selectedProjectKey.value = key
  showMobileSidebar.value = false
}

const handleRefresh = () => loadData(true)

// Optimistic delete
const handleDeleteMessage = async (id) => {
  const index = messages.value.findIndex(m => m.id === id)
  if (index === -1) return

  const backup = messages.value[index]
  messages.value.splice(index, 1)

  try {
    await fetchWithAuth(`/messages/${id}`, { method: 'DELETE' })
    message.success('已删除')
  } catch (e) {
    messages.value.splice(index, 0, backup)
    message.error('删除失败：' + e.message)
  }
}

// Batch delete
const handleBatchDelete = async () => {
  if (checkedRowKeys.value.length === 0) return

  const toDelete = [...checkedRowKeys.value]
  const backups = []

  toDelete.forEach(id => {
    const index = messages.value.findIndex(m => m.id === id)
    if (index !== -1) {
      backups.push({ index, item: messages.value[index] })
      messages.value.splice(index, 1)
    }
  })

  try {
    await Promise.all(
      toDelete.map(id => fetchWithAuth(`/messages/${id}`, { method: 'DELETE' }))
    )
    message.success(`已删除 ${toDelete.length} 条消息`)
    checkedRowKeys.value = []
  } catch (e) {
    backups.reverse().forEach(({ index, item }) => {
      messages.value.splice(index, 0, item)
    })
    message.error('批量删除失败：' + e.message)
  }
}

const handlePurge = async () => {
  try {
    const res = await fetchWithAuth(`/system/purge`, { method: 'DELETE' })
    const data = await res.json()
    message.success(`已清空 ${data.deleted_count} 条垃圾数据`)
    loadData(false)
  } catch (e) {
    message.error('清空失败：' + e.message)
  }
}

const handleToday = () => {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0)
  const end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999)
  dateRange.value = [start.getTime(), end.getTime()]
  loadData(true)
  showFilterDrawer.value = false
}

const handleDeleteProject = async (id) => {
  try {
    await fetchWithAuth(`/projects/${id}`, { method: 'DELETE' })
    message.success('项目已删除')
    if (selectedProjectKey.value === id) selectedProjectKey.value = 'all'
    loadData(false)
  } catch (e) {
    message.error('删除项目失败：' + e.message)
  }
}

const handleCopyProjectKey = async (project) => {
  try {
    await navigator.clipboard.writeText(project.api_key || project.id)
    message.success('已复制 API Key')
  } catch {
    message.error('复制失败')
  }
}

const getProjectMenuOptions = (project) => [
  { label: '复制 API Key', key: 'copy', icon: () => h(NIcon, null, { default: () => h(CopyOutline) }) },
  { type: 'divider' },
  { label: '删除项目', key: 'delete', icon: () => h(NIcon, null, { default: () => h(TrashOutline) }) }
]

const handleProjectAction = (key, project) => {
  if (key === 'copy') {
    handleCopyProjectKey(project)
  } else if (key === 'delete') {
    handleDeleteProject(project.id)
  }
}

const applyFilter = () => {
  showFilterDrawer.value = false
  loadData(true)
}

// Client-Side Computed Filtering
const filteredMessages = computed(() => {
  let result = messages.value

  if (selectedProjectKey.value !== 'all') {
    const p = projects.value.find(x => x.id === selectedProjectKey.value)
    const pName = p ? p.name : ''
    result = result.filter(m => m.project_name === pName)
  }

  if (filterLevel.value !== 'all') {
    result = result.filter(m => m.level === filterLevel.value)
  }

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
  total: filteredMessages.value.length,
  errors: messages.value.filter(m => m.level === 'error').length,
  projects: projects.value.length
}))

const rowKey = (row) => row.id

// Menu Options with Icons - flat structure for proper collapse behavior
const menuOptions = computed(() => {
  const projectItems = projects.value.map(p => ({
    label: p.name,
    key: p.id,
    icon: () => h(NIcon, null, { default: () => h(FolderOutline) }),
    extra: () => h(NDropdown, {
      options: getProjectMenuOptions(p),
      trigger: 'click',
      placement: 'bottom-end',
      onSelect: (key) => handleProjectAction(key, p)
    }, {
      default: () => h(NButton, {
        quaternary: true,
        circle: true,
        size: 'tiny',
        onClick: (e) => e.stopPropagation()
      }, { icon: () => h(NIcon, { size: 14 }, { default: () => h(EllipsisVertical) }) })
    })
  }))

  return [
    {
      label: '全部项目',
      key: 'all',
      icon: () => h(NIcon, null, { default: () => h(HomeOutline) })
    },
    {
      type: 'divider',
      key: 'd1'
    },
    ...projectItems
  ]
})

// Table Columns - responsive
const columns = computed(() => {
  const baseColumns = [
    { type: 'selection' },
    {
      title: '级别',
      key: 'level',
      width: 80,
      render(row) {
        const typeMap = { error: 'error', warning: 'warning', success: 'success', info: 'info' }
        const textMap = { error: '错误', warning: '警告', success: '成功', info: '信息' }
        return h(NTag, { type: typeMap[row.level] || 'default', bordered: false, round: true, size: 'small' }, { default: () => textMap[row.level] || row.level.toUpperCase() })
      }
    },
    { title: '来源', key: 'project_name', width: 100, ellipsis: true },
    {
      title: '标题',
      key: 'title',
      width: 160,
      ellipsis: { tooltip: true },
      render(row) {
        return h('b', {}, row.title)
      }
    },
    { title: '内容', key: 'content', ellipsis: { tooltip: { width: 300 } } },
    {
      title: '时间',
      key: 'created_at',
      width: 150,
      render: (row) => new Date(row.created_at).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'actions',
      width: 70,
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
            default: () => '确定删除?'
          }
        )
      }
    }
  ]
  return baseColumns
})

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

const toggleSidebar = () => {
  if (isMobile.value) {
    showMobileSidebar.value = !showMobileSidebar.value
  } else {
    collapsed.value = !collapsed.value
  }
}
</script>

<template>
  <n-layout has-sider class="layout-container">
    <!-- Desktop Sidebar -->
    <n-layout-sider
      v-if="!isMobile"
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="240"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      class="sidebar"
    >
      <div class="logo-area">
        <n-icon :size="collapsed ? 28 : 24" color="#3b82f6">
          <NotificationsOutline />
        </n-icon>
        <span v-if="!collapsed" class="logo-text">Notify Hub</span>
      </div>
      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="selectedProjectKey"
        @update:value="handleSwitchProject"
      />
      <div v-if="!collapsed" class="sidebar-footer">
        <n-popconfirm @positive-click="handlePurge">
          <template #trigger>
            <n-button block type="error" ghost size="medium">
              <template #icon>
                <n-icon><TrashOutline /></n-icon>
              </template>
              清空回收站
            </n-button>
          </template>
          确认彻底删除所有已标记删除的消息？
        </n-popconfirm>
      </div>
    </n-layout-sider>

    <!-- Mobile Sidebar Drawer -->
    <n-drawer v-model:show="showMobileSidebar" placement="left" :width="260">
      <n-drawer-content body-content-style="padding: 0;">
        <div class="logo-area">
          <n-icon :size="24" color="#3b82f6">
            <NotificationsOutline />
          </n-icon>
          <span class="logo-text">Notify Hub</span>
        </div>
        <n-menu
          :options="menuOptions"
          :value="selectedProjectKey"
          @update:value="handleMobileSwitchProject"
        />
        <div class="sidebar-footer">
          <n-popconfirm @positive-click="handlePurge">
            <template #trigger>
              <n-button block type="error" ghost size="medium">
                <template #icon>
                  <n-icon><TrashOutline /></n-icon>
                </template>
                清空回收站
              </n-button>
            </template>
            确认彻底删除？
          </n-popconfirm>
        </div>
      </n-drawer-content>
    </n-drawer>

    <n-layout>
      <n-layout-header bordered class="header">
        <div class="header-left">
          <!-- Mobile menu button -->
          <n-button v-if="isMobile" quaternary @click="toggleSidebar" class="menu-btn">
            <template #icon>
              <n-icon :size="22"><MenuOutline /></n-icon>
            </template>
          </n-button>
          <n-breadcrumb v-if="!isMobile">
            <n-breadcrumb-item>Notify Hub</n-breadcrumb-item>
            <n-breadcrumb-item>控制台</n-breadcrumb-item>
          </n-breadcrumb>
          <span v-else class="mobile-title">Notify Hub</span>
        </div>

        <div class="header-right">
          <span v-if="!isMobile" class="user-info">管理员</span>
          <n-button size="small" quaternary type="error" @click="handleLogout">
            退出
          </n-button>
        </div>
      </n-layout-header>

      <n-layout-content class="main-content">
        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card stat-card-blue">
            <div class="stat-icon">
              <n-icon :size="24"><NotificationsOutline /></n-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">当前展示</div>
            </div>
          </div>
          <div class="stat-card stat-card-red">
            <div class="stat-icon">
              <n-icon :size="24"><AlertCircleOutline /></n-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.errors }}</div>
              <div class="stat-label">异常报警</div>
            </div>
          </div>
          <div class="stat-card stat-card-green">
            <div class="stat-icon">
              <n-icon :size="24"><FolderOutline /></n-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.projects }}</div>
              <div class="stat-label">项目总数</div>
            </div>
          </div>
        </div>

        <!-- Filter Bar -->
        <n-card :bordered="false" class="filter-card" size="small">
          <div class="filter-row">
            <!-- Mobile: Filter button -->
            <template v-if="isMobile">
              <n-input
                v-model:value="searchText"
                placeholder="搜索..."
                clearable
                style="flex: 1"
              />
              <n-button @click="showFilterDrawer = true">
                <template #icon>
                  <n-icon><FilterOutline /></n-icon>
                </template>
              </n-button>
            </template>

            <!-- Desktop: Full filter row -->
            <template v-else>
              <n-select
                v-model:value="filterLevel"
                :options="[
                  { label: '全部级别', value: 'all' },
                  { label: '信息', value: 'info' },
                  { label: '成功', value: 'success' },
                  { label: '警告', value: 'warning' },
                  { label: '错误', value: 'error' }
                ]"
                size="medium"
                placeholder="级别"
                style="width: 120px"
              />

              <n-date-picker
                v-model:value="dateRange"
                type="datetimerange"
                clearable
                size="medium"
                placeholder="选择时间范围"
                style="width: 340px"
                @update:value="() => loadData(true)"
              />

              <n-select
                v-model:value="loadLimit"
                :options="[
                  { label: '近500条', value: 500 },
                  { label: '近1000条', value: 1000 },
                  { label: '近2000条', value: 2000 },
                  { label: '近5000条', value: 5000 }
                ]"
                size="medium"
                style="width: 110px"
                @update:value="() => loadData(true)"
              />

              <n-button strong secondary type="info" size="medium" @click="handleToday">
                今日
              </n-button>

              <n-input
                v-model:value="searchText"
                placeholder="搜索标题或内容..."
                clearable
                style="width: 200px"
              />

              <div style="flex: 1"></div>

              <n-popconfirm
                v-if="checkedRowKeys.length > 0"
                @positive-click="handleBatchDelete"
              >
                <template #trigger>
                  <n-button type="error" size="medium">
                    删除选中 ({{ checkedRowKeys.length }})
                  </n-button>
                </template>
                确定删除选中的 {{ checkedRowKeys.length }} 条消息吗？
              </n-popconfirm>
            </template>

            <n-button circle secondary type="primary" @click="handleRefresh" title="刷新">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
            </n-button>
          </div>
        </n-card>

        <!-- Main Table -->
        <n-card :bordered="false" class="table-card" size="medium">
          <template #header>
            <span style="font-weight: 600">消息列表</span>
          </template>
          <template #header-extra>
            <n-popconfirm v-if="selectedProjectKey !== 'all'" @positive-click="handleDeleteProject(selectedProjectKey)">
              <template #trigger>
                <n-button size="small" type="error" secondary>删除项目</n-button>
              </template>
              确认删除该项目吗？
            </n-popconfirm>
          </template>

          <template v-if="loading && messages.length === 0">
            <n-skeleton text :repeat="6" />
          </template>

          <n-data-table
            v-else
            :columns="columns"
            :data="filteredMessages"
            :loading="loading"
            :pagination="{ pageSize: isMobile ? 8 : 12 }"
            :max-height="isMobile ? 'calc(100vh - 360px)' : 'calc(100vh - 400px)'"
            :single-line="false"
            :row-key="rowKey"
            v-model:checked-row-keys="checkedRowKeys"
            :scroll-x="900"
            striped
          />
        </n-card>
      </n-layout-content>
    </n-layout>

    <!-- Mobile Filter Drawer -->
    <n-drawer v-model:show="showFilterDrawer" placement="bottom" :height="360">
      <n-drawer-content title="筛选条件">
        <n-space vertical size="large">
          <n-form-item label="级别">
            <n-select
              v-model:value="filterLevel"
              :options="[
                { label: '全部级别', value: 'all' },
                { label: '信息', value: 'info' },
                { label: '成功', value: 'success' },
                { label: '警告', value: 'warning' },
                { label: '错误', value: 'error' }
              ]"
            />
          </n-form-item>
          <n-form-item label="时间范围">
            <n-date-picker
              v-model:value="dateRange"
              type="datetimerange"
              clearable
              style="width: 100%"
            />
          </n-form-item>
          <n-form-item label="加载数量">
            <n-select
              v-model:value="loadLimit"
              :options="[
                { label: '近500条', value: 500 },
                { label: '近1000条', value: 1000 },
                { label: '近2000条', value: 2000 }
              ]"
            />
          </n-form-item>
          <n-space>
            <n-button type="info" @click="handleToday">今日</n-button>
            <n-button type="primary" @click="applyFilter">应用筛选</n-button>
          </n-space>
        </n-space>
      </n-drawer-content>
    </n-drawer>
  </n-layout>
</template>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background: #fff;
}

.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8fafc, #f0f9ff);
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-btn {
  margin-right: 4px;
}

.mobile-title {
  font-weight: 600;
  color: #3b82f6;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  font-size: 14px;
  color: #64748b;
}

.main-content {
  padding: 16px;
  background: #f8fafc;
  overflow-y: auto;
}

/* Stats Grid - Responsive */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .main-content {
    padding: 12px;
  }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.25s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.stat-card-blue .stat-icon {
  background: #eff6ff;
  color: #3b82f6;
}

.stat-card-red .stat-icon {
  background: #fef2f2;
  color: #ef4444;
}

.stat-card-green .stat-icon {
  background: #f0fdf4;
  color: #10b981;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

/* Filter Card */
.filter-card {
  margin-bottom: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* Table Card */
.table-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  background: #fff;
  margin-top: auto;
}

:deep(.n-data-table-tr--striped) {
  background: #fafafa;
}
</style>
