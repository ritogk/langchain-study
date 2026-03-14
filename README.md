# LangGraph 分岐パターン学習

LangGraph の4つのグラフ分岐パターンを実装・可視化し、LangSmith で品質評価を行う学習プロジェクト。

## 概要

LangGraph の分岐処理パターンを学び、各パターンの動作を Web UI で確認。
LangSmith 連携により、グラフの実行トレース・判断理由の可視化・ユースケース品質評価ができる。

### 4つの分岐パターン

| # | パターン | グラフ構造 | ユースケース |
|---|---------|-----------|-------------|
| 1 | 条件分岐 (Conditional) | 感情分析 → 3方向分岐 | カスタマーサポート振り分け |
| 2 | 並列分岐 (Fan-out/Fan-in) | 3つの分析を並列実行→統合 | コンテンツ分析パイプライン |
| 3 | LLMルーター | LLM判定 → 専門エージェント | インテリジェントFAQ |
| 4 | ループ付き分岐 | 生成→評価→改善ループ | 文章品質改善エージェント |

## フロー図

```mermaid
graph TB
    User[ユーザー] --> Web[Vue.js フロントエンド<br/>:5173]
    Web --> API[FastAPI バックエンド<br/>:8000]

    API --> P1[Pattern 1: 条件分岐]
    API --> P2[Pattern 2: 並列分岐]
    API --> P3[Pattern 3: LLMルーター]
    API --> P4[Pattern 4: ループ分岐]

    P1 --> LG[LangGraph StateGraph]
    P2 --> LG
    P3 --> LG
    P4 --> LG

    LG --> Claude[Claude API]
    LG --> LS[LangSmith トレーシング]

    API --> Eval[品質評価]
    Eval --> DS[データセット作成]
    DS --> LS
    Eval --> Judge[LLM-as-Judge]
    Judge --> LS
```

## ローカル環境構築手順

### 前提条件

- Docker / Docker Compose
- Anthropic API Key

### 1. 環境変数設定

`.env` に以下を設定:

```env
ANTHROPIC_API_KEY=your-api-key

# LangSmith（任意、品質評価機能を使う場合）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=langchain-study
```

### 2. 起動

```bash
docker compose up --build
```

### 3. アクセス

- フロントエンド: http://localhost:5173
- API (Swagger): http://localhost:8000/docs

## 本番デプロイ手順

（未実装 - ローカル動作確認後に CDK で構築予定）
