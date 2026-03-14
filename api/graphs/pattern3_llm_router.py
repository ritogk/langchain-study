"""
パターン3: LLMルーター (LLM-based Router)
LLMが質問のカテゴリを判定し、専門エージェントに振り分ける

グラフ構造:
  START → 質問分類 → (技術専門家 | ビジネス専門家 | クリエイティブ専門家) → 回答整形 → END
"""
import operator
import json
from typing import Annotated, Literal, TypedDict

from langgraph.graph import StateGraph, START, END

try:
    from .utils import get_llm
except ImportError:
    from graphs.utils import get_llm


class RouterState(TypedDict):
    question: str
    category: str
    reasoning: str
    expert_answer: str
    formatted_answer: str
    trace: Annotated[list[str], operator.add]


def classify_question(state: RouterState) -> dict:
    """LLMで質問カテゴリを分類"""
    llm = get_llm(temperature=0)
    result = llm.invoke(
        f"""以下の質問を分類してください。

質問: {state["question"]}

カテゴリ: tech (技術・プログラミング), business (ビジネス・経営), creative (クリエイティブ・デザイン)

JSON形式で回答（他のテキスト不要）:
{{"category": "tech" or "business" or "creative", "reasoning": "分類理由を日本語で"}}"""
    )
    content = result.content
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    parsed = json.loads(content.strip())
    return {
        "category": parsed["category"],
        "reasoning": parsed["reasoning"],
        "trace": ["質問分類"],
    }


def tech_expert(state: RouterState) -> dict:
    """技術専門家としての回答"""
    llm = get_llm()
    result = llm.invoke(
        f"あなたは技術専門家です。以下の技術的な質問に、具体的なコード例や技術的な詳細を含めて回答してください。\n\n質問: {state['question']}"
    )
    return {"expert_answer": result.content, "trace": ["技術専門家"]}


def business_expert(state: RouterState) -> dict:
    """ビジネス専門家としての回答"""
    llm = get_llm()
    result = llm.invoke(
        f"あなたはビジネスコンサルタントです。以下のビジネスに関する質問に、戦略的な視点と実践的なアドバイスを含めて回答してください。\n\n質問: {state['question']}"
    )
    return {"expert_answer": result.content, "trace": ["ビジネス専門家"]}


def creative_expert(state: RouterState) -> dict:
    """クリエイティブ専門家としての回答"""
    llm = get_llm()
    result = llm.invoke(
        f"あなたはクリエイティブディレクターです。以下のクリエイティブに関する質問に、インスピレーションと実践的な提案を含めて回答してください。\n\n質問: {state['question']}"
    )
    return {"expert_answer": result.content, "trace": ["クリエイティブ専門家"]}


def format_answer(state: RouterState) -> dict:
    """専門家の回答をフォーマット"""
    category_labels = {"tech": "技術", "business": "ビジネス", "creative": "クリエイティブ"}
    label = category_labels.get(state["category"], state["category"])
    formatted = f"**[{label}専門家の回答]**\n\n{state['expert_answer']}"
    return {"formatted_answer": formatted, "trace": ["回答整形"]}


def route_to_expert(state: RouterState) -> Literal["技術専門家", "ビジネス専門家", "クリエイティブ専門家"]:
    category = state.get("category", "tech")
    if category == "business":
        return "ビジネス専門家"
    elif category == "creative":
        return "クリエイティブ専門家"
    return "技術専門家"


def build_graph():
    builder = StateGraph(RouterState)

    builder.add_node("質問分類", classify_question)
    builder.add_node("技術専門家", tech_expert)
    builder.add_node("ビジネス専門家", business_expert)
    builder.add_node("クリエイティブ専門家", creative_expert)
    builder.add_node("回答整形", format_answer)

    builder.add_edge(START, "質問分類")
    builder.add_conditional_edges("質問分類", route_to_expert)
    builder.add_edge("技術専門家", "回答整形")
    builder.add_edge("ビジネス専門家", "回答整形")
    builder.add_edge("クリエイティブ専門家", "回答整形")
    builder.add_edge("回答整形", END)

    return builder.compile()


graph = build_graph()
