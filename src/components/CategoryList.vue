<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">分类</h2>
    <ul class="space-y-2">
      <li 
        v-for="category in categories" 
        :key="category"
        @click="$emit('select-category', category)"
        :class="[
          'px-4 py-2 rounded cursor-pointer transition-colors',
          selectedCategory === category 
            ? 'bg-blue-500 text-white' 
            : 'hover:bg-gray-100'
        ]"
      >
        {{ category === 'all' ? '全部' : category }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  props: {
    categories: {
      type: Array,
      required: true
    },
    selectedCategory: {
      type: String,
      required: true
    }
  },
  emits: ['select-category']
};
</script> 