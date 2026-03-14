<script setup>
import { ref, onMounted } from 'vue'

const useCases = ref({})
const selectedPattern = ref('')
const loading = ref(false)
const results = ref(null)
const langsmithAvailable = ref(null)

onMounted(async () => {
  const res = await fetch('/api/eval/use-cases')
  useCases.value = await res.json()
  // 最初のパターンを選択
  const keys = Object.keys(useCases.value)
  if (keys.length > 0) selectedPattern.value = keys[0]
})

async function runLocalEval() {
  if (!selectedPattern.value) return
  loading.value = true
  results.value = null
  try {
    const res = await fetch(`/api/eval/run-local/${selectedPattern.value}`, { method: 'POST' })
    results.value = await res.json()
  } catch (e) {
    results.value = { error: e.message }
  } finally {
    loading.value = false
  }
}

async function runLangSmithEval() {
  if (!selectedPattern.value) return
  loading.value = true
  results.value = null
  try {
    // まずデータセット作成
    await fetch(`/api/eval/create-dataset/${selectedPattern.value}`, { method: 'POST' })
    // 評価実行
    const res = await fetch(`/api/eval/run/${selectedPattern.value}`, { method: 'POST' })
    results.value = await res.json()
  } catch (e) {
    results.value = { error: e.message }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="eval-runner">
    <h2>品質評価 (Evaluation)</h2>
    <p class="desc">
      ユースケースを定義してグラフの判断精度を評価します。
      ローカル評価は API Key 不要、LangSmith 評価は LANGCHAIN_API_KEY が必要です。
    </p>

    <!-- パターン選択 -->
    <div class="select-group">
      <label>評価対象パターン:</label>
      <select v-model="selectedPattern">
        <option v-for="(uc, key) in useCases" :key="key" :value="key">
          {{ uc.name }} ({{ uc.example_count }}件)
        </option>
      </select>
    </div>

    <!-- ユースケース詳細 -->
    <div v-if="selectedPattern && useCases[selectedPattern]" class="use-case-info">
      <p>{{ useCases[selectedPattern].description }}</p>
      <p class="count">テストケース数: {{ useCases[selectedPattern].example_count }}件</p>
    </div>

    <!-- 実行ボタン -->
    <div class="button-group">
      <button @click="runLocalEval" :disabled="loading || !selectedPattern" class="btn-local">
        {{ loading ? '実行中...' : 'ローカル評価実行' }}
      </button>
      <button @click="runLangSmithEval" :disabled="loading || !selectedPattern" class="btn-langsmith">
        {{ loading ? '実行中...' : 'LangSmith 評価実行' }}
      </button>
    </div>

    <!-- 結果表示 -->
    <div v-if="results" class="results">
      <div v-if="results.error" class="error">{{ results.error }}</div>

      <template v-else>
        <!-- 精度サマリ -->
        <div v-if="results.accuracy !== undefined" class="accuracy-summary">
          <div class="accuracy-circle" :class="{ good: results.accuracy >= 0.8 }">
            {{ Math.round(results.accuracy * 100) }}%
          </div>
          <div>
            <p class="accuracy-label">正解率</p>
            <p class="accuracy-detail">{{ results.correct }} / {{ results.total }} 正解</p>
          </div>
        </div>

        <!-- LangSmith メッセージ -->
        <div v-if="results.message" class="langsmith-msg">
          {{ results.message }}
        </div>

        <!-- 個別結果 -->
        <div v-if="results.results" class="result-list">
          <h3>個別結果</h3>
          <div
            v-for="(r, i) in results.results"
            :key="i"
            class="result-item"
            :class="{ correct: r.match, incorrect: r.match === false }"
          >
            <div class="result-header">
              <span class="status">{{ r.match ? '正解' : r.match === false ? '不正解' : '-' }}</span>
              <span class="input-preview">{{ r.input }}</span>
            </div>
            <div class="result-body">
              <div v-if="r.expected" class="row">
                <span class="label">期待値:</span> {{ r.expected }}
              </div>
              <div v-if="r.actual" class="row">
                <span class="label">実際:</span> {{ r.actual }}
              </div>
              <div v-if="r.reasoning" class="row reasoning">
                <span class="label">判断理由:</span> {{ r.reasoning }}
              </div>
              <div v-if="r.response" class="row">
                <span class="label">応答:</span> {{ r.response }}
              </div>
              <!-- LangSmith 結果 -->
              <div v-if="r.scores" class="row">
                <span class="label">スコア:</span>
                <span v-for="(score, key) in r.scores" :key="key">
                  {{ key }}: {{ score }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.eval-runner {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 1.5rem;
}

h2 {
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
  color: #f1f5f9;
}

.desc {
  color: #94a3b8;
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
}

.select-group {
  margin-bottom: 1rem;
}

.select-group label {
  color: #94a3b8;
  font-size: 0.85rem;
  display: block;
  margin-bottom: 0.5rem;
}

select {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  color: #e2e8f0;
  font-size: 0.9rem;
  width: 100%;
}

.use-case-info {
  background: #0f172a;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #94a3b8;
}

.count {
  color: #64748b;
  margin-top: 0.25rem;
}

.button-group {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.btn-local {
  padding: 0.75rem 1.5rem;
  border: 1px solid #334155;
  border-radius: 8px;
  background: #1e293b;
  color: #e2e8f0;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-local:hover:not(:disabled) {
  border-color: #60a5fa;
}

.btn-langsmith {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #8b5cf6, #3b82f6);
  color: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-langsmith:hover:not(:disabled) {
  opacity: 0.9;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  background: #7f1d1d;
  color: #fca5a5;
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.accuracy-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #0f172a;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.accuracy-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 3px solid #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 700;
  color: #ef4444;
}

.accuracy-circle.good {
  border-color: #10b981;
  color: #10b981;
}

.accuracy-label {
  color: #94a3b8;
  font-size: 0.85rem;
}

.accuracy-detail {
  color: #e2e8f0;
  font-size: 1rem;
  font-weight: 600;
}

.langsmith-msg {
  background: #1a1a2e;
  border-left: 3px solid #8b5cf6;
  padding: 0.75rem 1rem;
  color: #c4b5fd;
  font-size: 0.85rem;
  border-radius: 0 8px 8px 0;
  margin-bottom: 1rem;
}

.result-list h3 {
  color: #94a3b8;
  font-size: 1rem;
  margin-bottom: 0.75rem;
}

.result-item {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  overflow: hidden;
}

.result-item.correct { border-left: 3px solid #10b981; }
.result-item.incorrect { border-left: 3px solid #ef4444; }

.result-header {
  display: flex;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background: #1e293b;
  font-size: 0.85rem;
}

.status {
  font-weight: 600;
  min-width: 50px;
}

.correct .status { color: #10b981; }
.incorrect .status { color: #ef4444; }

.input-preview {
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-body {
  padding: 0.5rem 1rem;
}

.row {
  font-size: 0.85rem;
  padding: 0.25rem 0;
  color: #e2e8f0;
}

.row .label {
  color: #64748b;
  margin-right: 0.5rem;
}

.reasoning {
  color: #c4b5fd;
}
</style>
