# LangChain / LangGraph 学習プロジェクト

## ドキュメント参照方針

実装前に必ず公式ドキュメントを確認すること。

- **LangChain**: `mcp__docs-langchain__search_docs_by_lang_chain` ツールを使って公式ドキュメントを検索・参照する
- **LangGraph**: 同ツールで LangGraph のドキュメントも検索できる

実装したい機能・クラス・関数がある場合は、コードを書く前にドキュメントを検索し、最新の API や推奨パターンを確認すること。

## 実装方針

### 標準関数・標準機能を優先する

- LangChain / LangGraph が提供する標準のクラス・関数・チェーンを最大限活用する
- 自前実装（カスタムクラス、独自ユーティリティ）は標準機能で実現できない場合のみ行う
- `LCEL (LangChain Expression Language)` のパイプ演算子 `|` を積極的に使う
- 組み込みのメモリ、ツール、エージェント、リトリーバーを優先して使用する

### ファイル粒度

1 ファイル = 1 コンセプト を基本とする。以下の粒度を守ること：

```
step1_<topic>.py     # 単一の概念・機能を学ぶスクリプト
step2_<topic>.py
...
```

- 1ファイルに複数の無関係な概念を詰め込まない
- 関連する補助関数・設定は同ファイル内の上部にまとめる
- 再利用する共通処理（モデル初期化など）は `utils.py` に切り出す
- サブトピックが多い場合はディレクトリを切る（例: `rag/`, `agents/`）

### LangSmith トレーシング

すべての実装で LangSmith によるトレーシング・可視化を有効にすること。

**必須設定（`.env` に記載）:**

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=<your-api-key>
LANGCHAIN_PROJECT=langchain-study   # プロジェクト名は用途に応じて変更可
```

**実装ルール:**

- `langsmith` パッケージを依存に含める
- 上記環境変数をセットするだけで LangChain / LangGraph の呼び出しは自動的にトレースされる
- カスタム関数をトレース対象にしたい場合は `@traceable` デコレータを使う
- `run_name` や `tags` を活用してトレースに意味のある名前を付ける
- LangGraph のグラフは LangSmith 上でステップごとの入出力・レイテンシが可視化されるので積極的に活用する

### コードスタイル

- 学習目的のため、各ステップに簡潔なコメントを入れる
- 実行して結果が確認できる `if __name__ == "__main__":` ブロックを必ず入れる
- 環境変数は `.env` から `python-dotenv` で読み込む
