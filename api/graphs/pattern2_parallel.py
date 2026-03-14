"""
パターン2: 並列分岐 (Fan-out / Fan-in)
入力テキストを3つの分析ノードに並列で送り、結果を統合する

グラフ構造:
  START → 分配 → (要約 & キーワード抽出 & 英語翻訳) → 統合 → END
"""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

try:
    from .utils import get_llm
except ImportError:
    from graphs.utils import get_llm


# --- State 定義 ---
class ParallelState(TypedDict):
    input_text: str
    summary: str
    keywords: str
    translation: str
    final_report: str
    trace: Annotated[list[str], operator.add]


# --- ノード定義 ---
def split(state: ParallelState) -> dict:
    """入力を受け取り、並列処理へ送る準備"""
    return {"trace": ["分配"]}


def summarize(state: ParallelState) -> dict:
    """テキストを要約"""
    llm = get_llm()
    result = llm.invoke(f"以下のテキストを3文以内で要約してください:\n\n{state['input_text']}")
    return {"summary": result.content, "trace": ["要約"]}


def extract_keywords(state: ParallelState) -> dict:
    """キーワードを抽出"""
    llm = get_llm(temperature=0)
    result = llm.invoke(f"以下のテキストから重要なキーワードを5個抽出し、カンマ区切りで列挙してください:\n\n{state['input_text']}")
    return {"keywords": result.content, "trace": ["キーワード抽出"]}


def translate(state: ParallelState) -> dict:
    """英語に翻訳"""
    llm = get_llm()
    result = llm.invoke(f"以下の日本語テキストを英語に翻訳してください。翻訳文のみ出力:\n\n{state['input_text']}")
    return {"translation": result.content, "trace": ["英語翻訳"]}


def aggregate(state: ParallelState) -> dict:
    """並列処理の結果を統合"""
    report = f"""## 分析レポート

### 要約
{state.get('summary', 'N/A')}

### キーワード
{state.get('keywords', 'N/A')}

### 英語翻訳
{state.get('translation', 'N/A')}"""
    return {"final_report": report, "trace": ["統合"]}


# --- グラフ構築 ---
def build_graph():
    builder = StateGraph(ParallelState)

    builder.add_node("分配", split)
    builder.add_node("要約", summarize)
    builder.add_node("キーワード抽出", extract_keywords)
    builder.add_node("英語翻訳", translate)
    builder.add_node("統合", aggregate)

    builder.add_edge(START, "分配")
    builder.add_edge("分配", "要約")
    builder.add_edge("分配", "キーワード抽出")
    builder.add_edge("分配", "英語翻訳")
    builder.add_edge("要約", "統合")
    builder.add_edge("キーワード抽出", "統合")
    builder.add_edge("英語翻訳", "統合")
    builder.add_edge("統合", END)

    return builder.compile()


graph = build_graph()
