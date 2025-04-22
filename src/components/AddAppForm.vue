<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">添加新应用</h2>
    
    <form @submit.prevent="saveApp" class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- 应用名称 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">应用名称</label>
          <input 
            v-model="form.name" 
            type="text" 
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入应用名称"
          >
        </div>
        
        <!-- 分类 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
          <input 
            v-model="form.category" 
            type="text" 
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入分类名称"
          >
        </div>
        
        <!-- 应用类型 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">应用类型</label>
          <select 
            v-model="form.type"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="software">软件</option>
            <option value="browser">浏览器</option>
          </select>
        </div>
        
        <!-- 软件路径或浏览器类型 -->
        <div v-if="form.type === 'software'" class="md:col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">软件路径</label>
          <div class="flex items-center space-x-2">
            <input 
              v-model="form.path" 
              type="text" 
              required
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="输入软件完整路径或拖放软件到下方区域"
            >
            <button 
              type="button"
              @click="browseSoftware"
              class="px-3 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              浏览
            </button>
          </div>
          
          <!-- 拖放区域 -->
          <div class="mt-2">
            <DragDropZone @file-selected="onFileSelected" />
          </div>
        </div>
        
        <div v-if="form.type === 'browser'">
          <label class="block text-sm font-medium text-gray-700 mb-1">浏览器类型</label>
          <select 
            v-model="form.browser"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="edge">Microsoft Edge</option>
            <option value="chrome">Google Chrome</option>
          </select>
        </div>
        
        <!-- 软件参数或网址 -->
        <div v-if="form.type === 'software'">
          <label class="block text-sm font-medium text-gray-700 mb-1">启动参数 (可选)</label>
          <input 
            v-model="form.args" 
            type="text" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入启动参数"
          >
        </div>
        
        <div v-if="form.type === 'browser'">
          <label class="block text-sm font-medium text-gray-700 mb-1">网址</label>
          <input 
            v-model="form.url" 
            type="url" 
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入网址"
          >
        </div>
      </div>
      
      <div class="flex justify-end">
        <button 
          type="submit"
          class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          添加应用
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { reactive } from 'vue';
import DragDropZone from './DragDropZone.vue';

export default {
  components: {
    DragDropZone
  },
  emits: ['save-app'],
  setup(props, { emit }) {
    const form = reactive({
      name: '',
      category: '',
      type: 'software',
      path: '',
      args: '',
      browser: 'edge',
      url: ''
    });
    
    const onFileSelected = (filePath) => {
      form.path = filePath;
      // 如果用户还没有输入名称，自动使用文件名作为应用名称
      if (!form.name) {
        // 使用 electronAPI 提供的函数
        if (window.electronAPI && window.electronAPI.getBasename) {
          form.name = window.electronAPI.getBasename(filePath, '.exe');
        } else {
          // 备用方法
          const fileName = filePath.split(/[\/\\]/).pop();
          const nameWithoutExt = fileName.replace(/\.[^/.]+$/, "");
          form.name = nameWithoutExt;
        }
      }
    };
    
    const browseSoftware = async () => {
      try {
        // 这里需要使用Electron的dialog API，但在渲染进程中需要通过preload脚本暴露
        // 假设我们已经在preload.js中暴露了这个API
        const result = await window.electronAPI.openFileDialog();
        if (result && !result.canceled && result.filePaths.length > 0) {
          onFileSelected(result.filePaths[0]);
        }
      } catch (error) {
        console.error('选择文件失败:', error);
      }
    };
    
    const saveApp = () => {
      emit('save-app', { ...form });
      
      // 重置表单
      form.name = '';
      form.category = '';
      form.path = '';
      form.args = '';
      form.url = '';
    };
    
    return {
      form,
      saveApp,
      onFileSelected,
      browseSoftware
    };
  }
};
</script> 