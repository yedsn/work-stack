<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-4">测试页面</h1>
    <p class="mb-4">如果您能看到这个页面，说明基本环境已经正常工作。</p>
    
    <button 
      @click="testElectronAPI" 
      class="px-4 py-2 bg-blue-500 text-white rounded"
    >
      测试 Electron API
    </button>
    
    <div v-if="apiResult" class="mt-4 p-4 bg-gray-100 rounded">
      <pre>{{ apiResult }}</pre>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  setup() {
    const apiResult = ref('');
    
    const testElectronAPI = async () => {
      try {
        if (window.electronAPI) {
          apiResult.value = '可用的 Electron API:\n';
          for (const key in window.electronAPI) {
            apiResult.value += `- ${key}\n`;
          }
        } else {
          apiResult.value = 'Electron API 不可用';
        }
      } catch (error) {
        apiResult.value = `错误: ${error.message}`;
      }
    };
    
    return {
      apiResult,
      testElectronAPI
    };
  }
};
</script> 