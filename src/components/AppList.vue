<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">应用列表</h2>
    
    <div v-if="apps.length === 0" class="text-center py-8 text-gray-500">
      暂无应用，请添加新应用
    </div>
    
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppItem 
        v-for="app in apps" 
        :key="app.id" 
        :app="app"
        @launch="$emit('launch-app', app)"
        @delete="$emit('delete-app', app.id)"
      />
    </div>
  </div>
</template>

<script>
import AppItem from './AppItem.vue';

export default {
  components: {
    AppItem
  },
  props: {
    apps: {
      type: Array,
      required: true
    }
  },
  emits: ['launch-app', 'delete-app']
};
</script> 