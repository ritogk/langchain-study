<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import MermaidDiagram from './MermaidDiagram.vue'

const props = defineProps({ pattern: Object })

const inputText = ref('')
const result = ref(null)
const loading = ref(false)
const mermaidCode = ref('')
const showExecuted = ref(false)

// パターンごとのプレースホルダー
const placeholders = {
  1: 'テキストを入力してください（例: この商品最高です！）',
  2: 'テキストを入力してください（例: LangGraphは分岐処理を可視化できるフレームワークです）',
  3: '質問を入力してください（例: Pythonでデコレータの使い方は？）',
  4: 'トピックを入力してください（例: AIの未来について）',
}

watch(() => props.pattern, () => {
  result.value = null
  inputText.value = ''
  showExecuted.value = false
  loadGraph()
})

onMounted(() => loadGraph())

async function loadGraph() {
  try {
    const res = await fetch(`/api/patterns/${props.pattern.id}/graph`)
    const data = await res.json()
    mermaidCode.value = data.mermaid
  } catch (e) {
    console.error('Failed to load graph:', e)
  }
}

async function run() {
  loading.value = true
  result.value = null
  try {
    const body = props.pattern.id === 3
      ? { question: inputText.value }
      : props.pattern.id === 4
        ? { topic: inputText.value, max_iterations: 3 }
        : { input_text: inputText.value }

    const res = await fetch(`/api/patterns/${props.pattern.id}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    result.value = await res.json()
    showExecuted.value = true // 実行後は自動で実行フロー表示
  } catch (e) {
    result.value = { error: e.message }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="runner">
    <h2>{{ pattern.name }}</h2>

    <!-- グラフ可視化 -->
    <div class="section">
      <h3>グラフ構造</h3>
      <div class="graph-toggle" v-if="result?.executed_mermaid">
        <button
          :class="{ active: !showExecuted }"
          @click="showExecuted = false"
        >全体</button>
        <button
          :class="{ active: showExecuted }"
          @click="showExecuted = true"
        >実行フロー</button>
      </div>
      <MermaidDiagram
        v-if="mermaidCode"
        :code="showExecuted && result?.executed_mermaid ? result.executed_mermaid : mermaidCode"
      />
    </div>

    <!-- 入力フォーム -->
    <div class="section">
      <h3>実行</h3>
      <div class="input-group">
        <textarea
          v-model="inputText"
          :placeholder="placeholders[pattern.id]"
          rows="3"
        ></textarea>
        <button @click="run" :disabled="loading || !inputText.trim()">
          {{ loading ? '実行中...' : '実行' }}
        </button>
      </div>
    </div>

    <!-- 結果表示 -->
    <div v-if="result" class="section">
      <h3>実行結果</h3>

      <!-- 実行パス -->
      <div v-if="result.trace" class="trace">
        <span class="trace-label">実行パス:</span>
        <span v-for="(step, i) in result.trace" :key="i" class="trace-step">
          {{ step }}
          <span v-if="i < result.trace.length - 1" class="arrow">&rarr;</span>
        </span>
      </div>

      <!-- 判断理由 -->
      <div v-if="result.reasoning" class="reasoning">
        <h4>判断理由</h4>
        <p>{{ result.reasoning }}</p>
      </div>

      <!-- パターン別結果 -->
      <div class="result-detail">
        <!-- Pattern 1 -->
        <template v-if="pattern.id === 1">
          <div class="result-row">
            <span class="key">感情:</span>
            <span class="value badge-inline" :class="result.sentiment">
              {{ result.sentiment }}
            </span>
          </div>
          <div class="result-row">
            <span class="key">応答:</span>
            <span class="value">{{ result.response }}</span>
          </div>
        </template>

        <!-- Pattern 2 -->
        <template v-if="pattern.id === 2">
          <div class="result-row"><span class="key">要約:</span><span class="value">{{ result.summary }}</span></div>
          <div class="result-row"><span class="key">キーワード:</span><span class="value">{{ result.keywords }}</span></div>
          <div class="result-row"><span class="key">英訳:</span><span class="value">{{ result.translation }}</span></div>
        </template>

        <!-- Pattern 3 -->
        <template v-if="pattern.id === 3">
          <div class="result-row">
            <span class="key">カテゴリ:</span>
            <span class="value badge-inline" :class="result.category">{{ result.category }}</span>
          </div>
          <div class="result-row">
            <span class="key">回答:</span>
            <span class="value markdown" v-html="marked(result.formatted_answer || '')"></span>
          </div>
        </template>

        <!-- Pattern 4 -->
        <template v-if="pattern.id === 4">
          <div class="result-row"><span class="key">スコア:</span><span class="value">{{ result.score }}/10</span></div>
          <div class="result-row"><span class="key">イテレーション:</span><span class="value">{{ result.iteration }}回</span></div>
          <div class="result-row"><span class="key">評価:</span><span class="value">{{ result.evaluation }}</span></div>
          <div class="result-row">
            <span class="key">最終出力:</span>
            <span class="value markdown" v-html="marked(result.final_output || '')"></span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.runner {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 1.5rem;
}

h2 {
  font-size: 1.3rem;
  margin-bottom: 1.5rem;
  color: #f1f5f9;
}

.section {
  margin-bottom: 1.5rem;
}

h3 {
  font-size: 1rem;
  color: #94a3b8;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid #334155;
  padding-bottom: 0.5rem;
}

.graph-toggle {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.graph-toggle button {
  padding: 0.35rem 1rem;
  border: 1px solid #334155;
  border-radius: 6px;
  background: #0f172a;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.graph-toggle button.active {
  background: #065f46;
  color: #6ee7b7;
  border-color: #10b981;
}

.graph-toggle button:hover:not(.active) {
  border-color: #60a5fa;
  color: #e2e8f0;
}

.input-group {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

textarea {
  flex: 1;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 0.75rem;
  color: #e2e8f0;
  font-size: 0.9rem;
  resize: vertical;
  font-family: inherit;
}

textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

button {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  white-space: nowrap;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #2563eb;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.trace {
  background: #0f172a;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.85rem;
}

.trace-label {
  color: #64748b;
  margin-right: 0.5rem;
}

.trace-step {
  color: #60a5fa;
}

.arrow {
  color: #475569;
  margin: 0 0.25rem;
}

.reasoning {
  background: #1a1a2e;
  border-left: 3px solid #a78bfa;
  padding: 0.75rem 1rem;
  border-radius: 0 8px 8px 0;
  margin-bottom: 1rem;
}

.reasoning h4 {
  color: #a78bfa;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.reasoning p {
  color: #c4b5fd;
  font-size: 0.9rem;
}

.result-row {
  display: flex;
  gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #1e293b;
}

.result-row:last-child {
  border-bottom: none;
}

.key {
  color: #64748b;
  min-width: 100px;
  flex-shrink: 0;
}

.value {
  color: #e2e8f0;
  line-height: 1.6;
}

.badge-inline {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.badge-inline.positive { background: #065f46; color: #6ee7b7; }
.badge-inline.negative { background: #7f1d1d; color: #fca5a5; }
.badge-inline.neutral { background: #1e3a5f; color: #93c5fd; }
.badge-inline.tech { background: #312e81; color: #a5b4fc; }
.badge-inline.business { background: #713f12; color: #fcd34d; }
.badge-inline.creative { background: #581c87; color: #d8b4fe; }

.markdown :deep(h1),
.markdown :deep(h2),
.markdown :deep(h3) {
  margin-top: 0.5rem;
}

.markdown :deep(code) {
  background: #0f172a;
  padding: 0.15rem 0.3rem;
  border-radius: 3px;
}

.markdown :deep(pre) {
  background: #0f172a;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
}

.result-detail {
  background: #0f172a;
  border-radius: 8px;
  padding: 1rem;
}
</style>
