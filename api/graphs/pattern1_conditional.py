"""
パターン1: 条件分岐 (Conditional Branch)
感情分析 → 結果に応じてポジティブ/ネガティブ/ニュートラルの応答ノードに分岐

グラフ構造:
  START → 感情分析 → (ポジティブ応答 | ネガティブ応答 | ニュートラル応答) → END
"""
import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import StateGraph, START, END

try:
    from .utils import get_llm
except ImportError:
    from graphs.utils import get_llm


# --- State 定義 ---
class SentimentState(TypedDict):
    input_text: str
    sentiment: str
    reasoning: str  # なぜその判断をしたか
    response: str
    trace: Annotated[list[str], operator.add]  # 実行パスを記録


# --- ノード定義 ---
def classify_sentiment(state: SentimentState) -> dict:
    """LLM で感情分析を実行"""
    llm = get_llm(temperature=0)
    result = llm.invoke(
        f"""以下のテキストの感情を分析してください。

テキスト: {state["input_text"]}

以下のJSON形式で回答してください（他のテキストは不要）:
{{"sentiment": "positive" or "negative" or "neutral", "reasoning": "判断理由を日本語で簡潔に"}}"""
    )

    import json
    content = result.content
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    parsed = json.loads(content.strip())

    return {
        "sentiment": parsed["sentiment"],
        "reasoning": parsed["reasoning"],
        "trace": ["感情分析"],
    }


def positive_response(state: SentimentState) -> dict:
    """ポジティブな入力に対する応答"""
    llm = get_llm()
    result = llm.invoke(
        f"ユーザーがポジティブな気持ちを表明しています。共感し、さらに良い気分にする短い応答を日本語で生成してください。\n入力: {state['input_text']}"
    )
    return {"response": result.content, "trace": ["ポジティブ応答"]}


def negative_response(state: SentimentState) -> dict:
    """ネガティブな入力に対する応答"""
    llm = get_llm()
    result = llm.invoke(
        f"ユーザーがネガティブな気持ちを表明しています。寄り添い、励ます短い応答を日本語で生成してください。\n入力: {state['input_text']}"
    )
    return {"response": result.content, "trace": ["ネガティブ応答"]}


def neutral_response(state: SentimentState) -> dict:
    """ニュートラルな入力に対する応答"""
    llm = get_llm()
    result = llm.invoke(
        f"ユーザーが中立的な内容を述べています。情報を補足する短い応答を日本語で生成してください。\n入力: {state['input_text']}"
    )
    return {"response": result.content, "trace": ["ニュートラル応答"]}


# --- ルーティング関数 ---
def route_by_sentiment(state: SentimentState) -> Literal["ポジティブ応答", "ネガティブ応答", "ニュートラル応答"]:
    """感情分析結果に基づいてルーティング"""
    sentiment = state.get("sentiment", "neutral")
    if sentiment == "positive":
        return "ポジティブ応答"
    elif sentiment == "negative":
        return "ネガティブ応答"
    return "ニュートラル応答"


# --- グラフ構築 ---
def build_graph():
    builder = StateGraph(SentimentState)

    builder.add_node("感情分析", classify_sentiment)
    builder.add_node("ポジティブ応答", positive_response)
    builder.add_node("ネガティブ応答", negative_response)
    builder.add_node("ニュートラル応答", neutral_response)

    builder.add_edge(START, "感情分析")
    builder.add_conditional_edges("感情分析", route_by_sentiment)
    builder.add_edge("ポジティブ応答", END)
    builder.add_edge("ネガティブ応答", END)
    builder.add_edge("ニュートラル応答", END)

    return builder.compile()


graph = build_graph()
