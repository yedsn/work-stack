<template>
  <div 
    class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors"
    :class="{ 'border-blue-500 bg-blue-50': isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="onDrop"
  >
    <div class="flex flex-col items-center justify-center">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <p class="mt-2 text-sm text-gray-600">拖放软件到此处，或点击浏览</p>
      <input 
        type="file" 
        ref="fileInput" 
        class="hidden" 
        @change="onFileSelected"
      >
      <button 
        type="button"
        @click="$refs.fileInput.click()"
        class="mt-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
      >
        浏览文件
      </button>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  emits: ['file-selected'],
  setup(props, { emit }) {
    const isDragging = ref(false);
    const fileInput = ref(null);
    
    const onDrop = (event) => {
      isDragging.value = false;
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        const file = files[0];
        emit('file-selected', file.path);
      }
    };
    
    const onFileSelected = (event) => {
      const files = event.target.files;
      if (files.length > 0) {
        const file = files[0];
        emit('file-selected', file.path);
      }
    };
    
    return {
      isDragging,
      fileInput,
      onDrop,
      onFileSelected
    };
  }
};
</script> 