<script setup>
defineProps({
  pattern: Object,
  selected: Boolean,
})
defineEmits(['select'])

const typeLabels = {
  conditional_edges: '条件分岐',
  fan_out_fan_in: '並列処理',
  llm_router: 'LLM判定',
  loop_with_condition: 'ループ',
}

const typeColors = {
  conditional_edges: '#f59e0b',
  fan_out_fan_in: '#10b981',
  llm_router: '#8b5cf6',
  loop_with_condition: '#ef4444',
}
</script>

<template>
  <div class="card" :class="{ selected }" @click="$emit('select', pattern)">
    <div class="card-header">
      <span class="badge" :style="{ background: typeColors[pattern.graph_type] }">
        {{ typeLabels[pattern.graph_type] }}
      </span>
      <span class="id">Pattern {{ pattern.id }}</span>
    </div>
    <h3>{{ pattern.name }}</h3>
    <p>{{ pattern.description }}</p>
    <div class="use-case">
      <span class="label">ユースケース:</span> {{ pattern.use_case }}
    </div>
  </div>
</template>

<style scoped>
.card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.card:hover {
  border-color: #60a5fa;
  transform: translateY(-2px);
}

.card.selected {
  border-color: #3b82f6;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.badge {
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  color: white;
  font-weight: 600;
}

.id {
  color: #64748b;
  font-size: 0.8rem;
}

h3 {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: #f1f5f9;
}

p {
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.use-case {
  font-size: 0.8rem;
  color: #64748b;
  border-top: 1px solid #334155;
  padding-top: 0.5rem;
}

.label {
  color: #94a3b8;
}
</style>
