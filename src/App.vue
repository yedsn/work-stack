<template>
  <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
    {{ error }}
  </div>
  <div class="min-h-screen bg-white p-4">
    <div class="max-w-6xl mx-auto">
      <header class="mb-6">
        <h1 class="text-3xl font-bold text-gray-800">应用启动管理工具</h1>
        <p class="text-gray-600">快速管理和启动您常用的应用和网站</p>
      </header>
      
      <!-- 顶部分类标签 -->
      <div class="flex space-x-4 mb-6 overflow-x-auto pb-2">
        <div 
          v-for="category in categories" 
          :key="category"
          @click="selectCategory(category)"
          :class="[
            'px-8 py-4 text-center border rounded-lg cursor-pointer transition-colors flex-shrink-0',
            selectedCategory === category 
              ? 'border-blue-500 bg-blue-50 text-blue-700' 
              : 'border-gray-300 hover:bg-gray-50'
          ]"
        >
          {{ category === 'all' ? '全部' : category }}
        </div>
        <div 
          class="px-8 py-4 text-center border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 flex-shrink-0"
          @click="showAddCategoryModal = true"
        >
          <span class="text-2xl">+</span>
        </div>
      </div>
      
      <!-- 应用列表区域 -->
      <div class="border border-gray-200 rounded-lg p-6 mb-6 min-h-[400px]">
        <div 
          class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors"
          :class="{ 'border-blue-500 bg-blue-50': isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
          v-if="filteredApps.length === 0"
        >
          <div class="flex flex-col items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="mt-2 text-sm text-gray-600">拖放软件到此处，或点击下方添加</p>
          </div>
        </div>
        
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div 
            v-for="app in filteredApps" 
            :key="app.id"
            class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow relative group"
          >
            <div 
              class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <button 
                @click.stop="deleteApp(app.id)" 
                class="p-1 text-gray-500 hover:text-red-500"
                title="删除"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
            
            <div @click="launchApp(app)" class="cursor-pointer">
              <h3 class="font-medium text-lg">{{ app.name }}</h3>
              <p class="text-sm text-gray-500 mt-1">
                应用: {{ app.type === 'software' ? '软件' : app.browser }}
              </p>
              <p class="text-sm text-gray-500 truncate">
                参数: {{ app.type === 'software' ? app.path : app.url }}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 底部添加表单 -->
      <div class="flex flex-wrap gap-2">
        <input 
          type="text" 
          placeholder="名称"
          v-model="newApp.name"
          class="flex-1 min-w-[150px] px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select 
          v-model="newApp.type"
          class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="software">软件</option>
          <option value="browser">浏览器</option>
        </select>
        <select 
          v-if="newApp.type === 'browser'"
          v-model="newApp.browser"
          class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="edge">Edge</option>
          <option value="chrome">Chrome</option>
        </select>
        <button 
          @click="browsePath"
          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          浏览
        </button>
        <input 
          type="text" 
          placeholder="参数"
          :value="newApp.type === 'software' ? newApp.args : newApp.url"
          @input="newApp.type === 'software' ? newApp.args = $event.target.value : newApp.url = $event.target.value"
          class="flex-1 min-w-[150px] px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select 
          v-model="newApp.category"
          class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option v-for="cat in categories.filter(c => c !== 'all')" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>
        <button 
          @click="addNewApp"
          class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          添加
        </button>
      </div>
    </div>
  </div>
  
  <!-- 添加分类模态框 -->
  <div v-if="showAddCategoryModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-full max-w-md">
      <h3 class="text-xl font-semibold mb-4">添加新分类</h3>
      <input 
        type="text" 
        v-model="newCategory"
        placeholder="输入分类名称"
        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
      />
      <div class="flex justify-end space-x-2">
        <button 
          @click="showAddCategoryModal = false"
          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          取消
        </button>
        <button 
          @click="addCategory"
          class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          添加
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, reactive, onBeforeUnmount } from 'vue';

export default {
  setup() {
    const apps = ref([]);
    const selectedCategory = ref('all');
    const error = ref('');
    const showAddCategoryModal = ref(false);
    const newCategory = ref('');
    const customCategories = ref(JSON.parse(localStorage.getItem('customCategories') || '["娱乐", "工作", "文档"]'));
    
    const newApp = reactive({
      name: '',
      category: '',
      type: 'software',
      path: '',
      args: '',
      browser: 'edge',
      url: ''
    });
    
    const isDragging = ref(false);
    
    // 检查 electronAPI 是否可用
    if (!window.electronAPI) {
      error.value = 'Electron API 不可用，请确保应用在 Electron 环境中运行';
      console.error(error.value);
    }
    
    // 从所有应用中提取唯一的分类，并合并自定义分类
    const categories = computed(() => {
      const appCategories = new Set(apps.value.map(app => app.category));
      const allCategories = new Set([...customCategories.value, ...appCategories]);
      return ['all', ...Array.from(allCategories)];
    });
    
    // 根据选定的分类过滤应用
    const filteredApps = computed(() => {
      if (selectedCategory.value === 'all') {
        return apps.value;
      }
      return apps.value.filter(app => app.category === selectedCategory.value);
    });
    
    // 选择分类
    const selectCategory = (category) => {
      selectedCategory.value = category;
    };
    
    // 添加新分类
    const addCategory = () => {
      if (newCategory.value && !customCategories.value.includes(newCategory.value)) {
        customCategories.value.push(newCategory.value);
        localStorage.setItem('customCategories', JSON.stringify(customCategories.value));
        newApp.category = newCategory.value;
        newCategory.value = '';
        showAddCategoryModal.value = false;
      }
    };
    
    // 加载应用列表
    const loadApps = async () => {
      try {
        if (!window.electronAPI) {
          error.value = 'Electron API 不可用';
          return;
        }
        apps.value = await window.electronAPI.getApps();
      } catch (err) {
        error.value = `加载应用失败: ${err.message}`;
        console.error(error.value, err);
      }
    };
    
    // 浏览文件路径
    const browsePath = async () => {
      try {
        if (newApp.type === 'software') {
          const result = await window.electronAPI.openFileDialog();
          if (result && !result.canceled && result.filePaths.length > 0) {
            newApp.path = result.filePaths[0];
            // 如果用户还没有输入名称，自动使用文件名作为应用名称
            if (!newApp.name) {
              if (window.electronAPI && window.electronAPI.getBasename) {
                newApp.name = await window.electronAPI.getBasename(newApp.path, '.exe');
              } else {
                const fileName = newApp.path.split(/[\/\\]/).pop();
                const nameWithoutExt = fileName.replace(/\.[^/.]+$/, "");
                newApp.name = nameWithoutExt;
              }
            }
          }
        }
      } catch (error) {
        console.error('选择文件失败:', error);
      }
    };
    
    // 添加新应用
    const addNewApp = async () => {
      if (!newApp.name) {
        error.value = '请输入应用名称';
        return;
      }
      
      if (newApp.type === 'software' && !newApp.path) {
        error.value = '请选择软件路径';
        return;
      }
      
      if (newApp.type === 'browser' && !newApp.url) {
        error.value = '请输入网址';
        return;
      }
      
      try {
        // 创建一个干净的对象副本
        const appToSave = {
          id: Date.now().toString(),
          name: newApp.name,
          type: newApp.type,
          category: newApp.category || '未分类',
          path: newApp.type === 'software' ? newApp.path : '',
          args: newApp.type === 'software' ? newApp.args : '',
          browser: newApp.type === 'browser' ? newApp.browser : 'edge',
          url: newApp.type === 'browser' ? newApp.url : ''
        };
        
        apps.value = await window.electronAPI.saveApp(appToSave);
        
        // 重置表单
        newApp.name = '';
        newApp.path = '';
        newApp.args = '';
        newApp.url = '';
        newApp.category = '';
        error.value = '';
      } catch (err) {
        error.value = `保存应用失败: ${err.message}`;
        console.error(error.value, err);
      }
    };
    
    // 删除应用
    const deleteApp = async (id) => {
      try {
        apps.value = await window.electronAPI.deleteApp(id);
      } catch (err) {
        error.value = `删除应用失败: ${err.message}`;
        console.error(error.value, err);
      }
    };
    
    // 启动应用
    const launchApp = async (app) => {
      try {
        // 创建一个可序列化的应用对象副本
        const appToLaunch = {
          id: app.id,
          name: app.name,
          type: app.type,
          category: app.category,
          path: app.type === 'software' ? app.path : '',
          args: app.type === 'software' ? app.args : '',
          browser: app.type === 'browser' ? app.browser : '',
          url: app.type === 'browser' ? app.url : ''
        };
        
        const result = await window.electronAPI.launchApp(appToLaunch);
        if (!result) {
          error.value = '启动应用失败';
        }
      } catch (err) {
        error.value = `启动应用失败: ${err.message}`;
        console.error(error.value, err);
      }
    };
    
    // 添加快捷键支持
    const handleKeyDown = (event) => {
      // Ctrl+N: 添加新应用
      if (event.ctrlKey && event.key === 'n') {
        event.preventDefault();
        // 聚焦到名称输入框
        document.querySelector('input[placeholder="名称"]').focus();
      }
      
      // Esc: 关闭模态框
      if (event.key === 'Escape' && showAddCategoryModal.value) {
        showAddCategoryModal.value = false;
      }
    };
    
    const onDrop = (event) => {
      isDragging.value = false;
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        const file = files[0];
        newApp.path = file.path;
        newApp.type = 'software';
        
        // 如果用户还没有输入名称，自动使用文件名作为应用名称
        if (!newApp.name) {
          if (window.electronAPI && window.electronAPI.getBasename) {
            window.electronAPI.getBasename(newApp.path, '.exe')
              .then(basename => {
                newApp.name = basename;
              });
          } else {
            const fileName = newApp.path.split(/[\/\\]/).pop();
            const nameWithoutExt = fileName.replace(/\.[^/.]+$/, "");
            newApp.name = nameWithoutExt;
          }
        }
      }
    };
    
    onMounted(() => {
      loadApps();
      window.addEventListener('keydown', handleKeyDown);
    });
    
    onBeforeUnmount(() => {
      window.removeEventListener('keydown', handleKeyDown);
    });
    
    return {
      apps,
      categories,
      selectedCategory,
      filteredApps,
      selectCategory,
      newApp,
      browsePath,
      addNewApp,
      deleteApp,
      launchApp,
      error,
      showAddCategoryModal,
      newCategory,
      addCategory,
      customCategories,
      isDragging,
      onDrop
    };
  }
};
</script>

<style>
/* 基础样式 */
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.min-h-screen {
  min-height: 100vh;
}

.bg-white {
  background-color: white;
}

.p-4 {
  padding: 1rem;
}

.max-w-6xl {
  max-width: 72rem;
}

.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.mb-6 {
  margin-bottom: 1.5rem;
}

.text-3xl {
  font-size: 1.875rem;
  line-height: 2.25rem;
}

.font-bold {
  font-weight: 700;
}

.text-gray-800 {
  color: #1f2937;
}

.text-gray-600 {
  color: #4b5563;
}

/* 分类标签样式 */
.flex {
  display: flex;
}

.space-x-4 > * + * {
  margin-left: 1rem;
}

.overflow-x-auto {
  overflow-x: auto;
}

.pb-2 {
  padding-bottom: 0.5rem;
}

.px-8 {
  padding-left: 2rem;
  padding-right: 2rem;
}

.py-4 {
  padding-top: 1rem;
  padding-bottom: 1rem;
}

.text-center {
  text-align: center;
}

.border {
  border-width: 1px;
  border-style: solid;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.cursor-pointer {
  cursor: pointer;
}

.transition-colors {
  transition-property: color, background-color, border-color;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.flex-shrink-0 {
  flex-shrink: 0;
}

.border-blue-500 {
  border-color: #3b82f6;
}

.bg-blue-50 {
  background-color: #eff6ff;
}

.text-blue-700 {
  color: #1d4ed8;
}

.border-gray-300 {
  border-color: #d1d5db;
}

.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
}

/* 应用列表区域样式 */
.border-gray-200 {
  border-color: #e5e7eb;
}

.min-h-\[400px\] {
  min-height: 400px;
}

.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.gap-4 {
  gap: 1rem;
}

.relative {
  position: relative;
}

.absolute {
  position: absolute;
}

.top-2 {
  top: 0.5rem;
}

.right-2 {
  right: 0.5rem;
}

.opacity-0 {
  opacity: 0;
}

.transition-opacity {
  transition-property: opacity;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.p-1 {
  padding: 0.25rem;
}

.text-gray-500 {
  color: #6b7280;
}

.hover\:text-red-500:hover {
  color: #ef4444;
}

.h-5 {
  height: 1.25rem;
}

.w-5 {
  width: 1.25rem;
}

.text-lg {
  font-size: 1.125rem;
  line-height: 1.75rem;
}

.mt-1 {
  margin-top: 0.25rem;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 表单样式 */
.flex-wrap {
  flex-wrap: wrap;
}

.gap-2 {
  gap: 0.5rem;
}

.flex-1 {
  flex: 1 1 0%;
}

.min-w-\[150px\] {
  min-width: 150px;
}

.focus\:outline-none:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
}

.focus\:ring-2:focus {
  --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);
  --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color);
  box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000);
}

.focus\:ring-blue-500:focus {
  --tw-ring-color: #3b82f6;
}

.bg-blue-500 {
  background-color: #3b82f6;
}

.text-white {
  color: white;
}

.hover\:bg-blue-600:hover {
  background-color: #2563eb;
}

/* 模态框样式 */
.fixed {
  position: fixed;
}

.inset-0 {
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.bg-black {
  background-color: #000;
}

.bg-opacity-50 {
  --tw-bg-opacity: 0.5;
}

.items-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.z-50 {
  z-index: 50;
}

.w-full {
  width: 100%;
}

.max-w-md {
  max-width: 28rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.justify-end {
  justify-content: flex-end;
}

.space-x-2 > * + * {
  margin-left: 0.5rem;
}

/* 错误提示样式 */
.bg-red-100 {
  background-color: #fee2e2;
}

.border-red-400 {
  border-color: #f87171;
}

.text-red-700 {
  color: #b91c1c;
}

.px-4 {
  padding-left: 1rem;
  padding-right: 1rem;
}

.py-3 {
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
}

.rounded {
  border-radius: 0.25rem;
}

/* 响应式布局 */
@media (min-width: 640px) {
  .sm\:grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 768px) {
  .md\:grid-cols-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

/* 自定义动画 */
.group:hover {
  transform: translateY(-2px);
  transition: transform 0.2s ease;
}

.group-hover\:opacity-100:hover {
  opacity: 1;
}

.hover\:shadow-md:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
</style> 