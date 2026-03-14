"""
パターン4: ループ付き分岐 (Loop with Exit Condition)
文章を改善するループ: 生成→評価→(改善が必要ならループ / 合格なら終了)

グラフ構造:
  START → 初稿生成 → 品質評価 → (文章改善 → 品質評価) or → 最終出力 → END
"""
import operator
import json
from typing import Annotated, Literal, TypedDict

from langgraph.graph import StateGraph, START, END

try:
    from .utils import get_llm
except ImportError:
    from graphs.utils import get_llm


class LoopState(TypedDict):
    topic: str
    draft: str
    evaluation: str
    score: int
    reasoning: str
    iteration: int
    max_iterations: int
    final_output: str
    trace: Annotated[list[str], operator.add]


def generate_draft(state: LoopState) -> dict:
    """トピックから初稿を生成"""
    llm = get_llm()
    result = llm.invoke(
        f"以下のトピックについて、200文字程度の短い文章を日本語で書いてください。\n\nトピック: {state['topic']}"
    )
    return {"draft": result.content, "iteration": 1, "trace": ["初稿生成"]}


def evaluate_quality(state: LoopState) -> dict:
    """文章の品質を評価（1-10 スコア）"""
    llm = get_llm(temperature=0)
    result = llm.invoke(
        f"""以下の文章の品質を評価してください。

文章:
{state["draft"]}

以下のJSON形式で回答（他のテキスト不要）:
{{"score": 1-10の整数, "evaluation": "改善点を具体的に日本語で", "reasoning": "このスコアを付けた理由"}}"""
    )
    content = result.content
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    parsed = json.loads(content.strip())
    return {
        "score": parsed["score"],
        "evaluation": parsed["evaluation"],
        "reasoning": parsed["reasoning"],
        "trace": [f"品質評価(スコア={parsed['score']}, 回目={state.get('iteration', 1)})"],
    }


def improve_draft(state: LoopState) -> dict:
    """評価に基づいて文章を改善"""
    llm = get_llm()
    result = llm.invoke(
        f"""以下の文章を、指摘された改善点に基づいて改善してください。

元の文章:
{state["draft"]}

改善点:
{state["evaluation"]}

改善した文章のみ出力してください。"""
    )
    return {
        "draft": result.content,
        "iteration": state.get("iteration", 1) + 1,
        "trace": [f"文章改善({state.get('iteration', 1) + 1}回目)"],
    }


def finalize(state: LoopState) -> dict:
    """最終出力を生成"""
    output = f"""## 最終文章
{state["draft"]}

---
**評価スコア**: {state["score"]}/10
**イテレーション回数**: {state.get("iteration", 1)}
**最終評価**: {state.get("reasoning", "")}"""
    return {"final_output": output, "trace": ["最終出力"]}


def should_continue(state: LoopState) -> Literal["文章改善", "最終出力"]:
    """品質基準（スコア7以上）を満たすかループ上限に達したら終了"""
    if state.get("score", 0) >= 7:
        return "最終出力"
    if state.get("iteration", 1) >= state.get("max_iterations", 3):
        return "最終出力"
    return "文章改善"


def build_graph():
    builder = StateGraph(LoopState)

    builder.add_node("初稿生成", generate_draft)
    builder.add_node("品質評価", evaluate_quality)
    builder.add_node("文章改善", improve_draft)
    builder.add_node("最終出力", finalize)

    builder.add_edge(START, "初稿生成")
    builder.add_edge("初稿生成", "品質評価")
    builder.add_conditional_edges("品質評価", should_continue)
    builder.add_edge("文章改善", "品質評価")
    builder.add_edge("最終出力", END)

    return builder.compile()


graph = build_graph()
