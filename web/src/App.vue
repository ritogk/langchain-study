<script setup>
import { ref, onMounted } from 'vue'
import PatternCard from './components/PatternCard.vue'
import PatternRunner from './components/PatternRunner.vue'
import EvalRunner from './components/EvalRunner.vue'

const patterns = ref([])
const selectedPattern = ref(null)
const activeTab = ref('patterns') // 'patterns' | 'eval'

onMounted(async () => {
  const res = await fetch('/api/patterns')
  patterns.value = await res.json()
})

function selectPattern(p) {
  selectedPattern.value = p
  activeTab.value = 'patterns'
}
</script>

<template>
  <div class="app">
    <header>
      <h1>LangGraph 分岐パターン学習</h1>
      <p class="subtitle">4つのグラフ分岐パターンを実行し、LangSmith で可視化・品質評価</p>
      <nav>
        <button :class="{ active: activeTab === 'patterns' }" @click="activeTab = 'patterns'">
          分岐パターン実行
        </button>
        <button :class="{ active: activeTab === 'eval' }" @click="activeTab = 'eval'">
          品質評価 (Evaluation)
        </button>
      </nav>
    </header>

    <main v-if="activeTab === 'patterns'">
      <div class="pattern-grid">
        <PatternCard
          v-for="p in patterns"
          :key="p.id"
          :pattern="p"
          :selected="selectedPattern?.id === p.id"
          @select="selectPattern(p)"
        />
      </div>

      <PatternRunner v-if="selectedPattern" :pattern="selectedPattern" />
    </main>

    <main v-else>
      <EvalRunner />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f172a;
  color: #e2e8f0;
  min-height: 100vh;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

header {
  text-align: center;
  margin-bottom: 2rem;
}

header h1 {
  font-size: 2rem;
  background: linear-gradient(135deg, #60a5fa, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #94a3b8;
  margin-bottom: 1.5rem;
}

nav {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

nav button {
  padding: 0.5rem 1.5rem;
  border: 1px solid #334155;
  border-radius: 8px;
  background: #1e293b;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

nav button.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

nav button:hover:not(.active) {
  border-color: #60a5fa;
  color: #e2e8f0;
}

.pattern-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
</style>
