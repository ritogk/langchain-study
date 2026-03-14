<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import mermaid from 'mermaid'

const props = defineProps({
  code: String,
})

const container = ref(null)
const uniqueId = ref(`mermaid-${Date.now()}`)

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#3b82f6',
    primaryTextColor: '#e2e8f0',
    primaryBorderColor: '#60a5fa',
    lineColor: '#64748b',
    secondaryColor: '#1e293b',
    tertiaryColor: '#0f172a',
  },
})

async function renderDiagram() {
  if (!props.code || !container.value) return
  try {
    uniqueId.value = `mermaid-${Date.now()}`
    const { svg } = await mermaid.render(uniqueId.value, props.code)
    container.value.innerHTML = svg
  } catch (e) {
    console.error('Mermaid render error:', e)
    container.value.innerHTML = `<pre style="color: #94a3b8; font-size: 0.8rem;">${props.code}</pre>`
  }
}

onMounted(() => renderDiagram())
watch(() => props.code, () => nextTick(renderDiagram))
</script>

<template>
  <div ref="container" class="mermaid-container"></div>
</template>

<style scoped>
.mermaid-container {
  background: #0f172a;
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
  text-align: center;
}

.mermaid-container :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>
