<template>
  <div class="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
    <div class="flex justify-between items-start">
      <div>
        <h3 class="font-medium text-lg">{{ app.name }}</h3>
        <p class="text-sm text-gray-600 mt-1">
          <span class="inline-block px-2 py-1 bg-gray-200 rounded-full text-xs mr-2">
            {{ app.category }}
          </span>
          {{ getAppDescription }}
        </p>
      </div>
      
      <div class="flex space-x-2">
        <button 
          @click="$emit('launch')"
          class="p-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          title="启动"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
          </svg>
        </button>
        
        <button 
          @click="$emit('delete')"
          class="p-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          title="删除"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  props: {
    app: {
      type: Object,
      required: true
    }
  },
  emits: ['launch', 'delete'],
  setup(props) {
    const getAppDescription = computed(() => {
      if (props.app.type === 'software') {
        return `软件: ${props.app.path}`;
      } else if (props.app.type === 'browser') {
        return `${props.app.browser}: ${props.app.url}`;
      }
      return '';
    });
    
    return {
      getAppDescription
    };
  }
};
</script> 