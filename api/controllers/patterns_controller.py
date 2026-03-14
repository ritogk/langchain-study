"""パターン一覧・グラフ取得・実行 API"""
import os
import uuid

from fastapi import APIRouter

from graphs.utils import get_mermaid, get_mermaid_with_trace
from graphs.pattern1_conditional import graph as graph1
from graphs.pattern2_parallel import graph as graph2
from graphs.pattern3_llm_router import graph as graph3
from graphs.pattern4_loop import graph as graph4

router = APIRouter()

GRAPHS = {1: graph1, 2: graph2, 3: graph3, 4: graph4}

RUN_NAMES = {
    1: "pattern1_conditional_branch",
    2: "pattern2_parallel_fanout",
    3: "pattern3_llm_router",
    4: "pattern4_loop_improve",
}

PATTERNS = [
    {
        "id": 1,
        "name": "条件分岐 (Conditional Branch)",
        "description": "感情分析の結果に基づいて、ポジティブ/ネガティブ/ニュートラルの応答生成ノードに分岐する",
        "graph_type": "conditional_edges",
        "use_case": "カスタマーサポートの自動振り分け",
    },
    {
        "id": 2,
        "name": "並列分岐 (Fan-out / Fan-in)",
        "description": "入力テキストを複数の分析ノード（要約・キーワード・翻訳）に並列で送り、結果を統合する",
        "graph_type": "fan_out_fan_in",
        "use_case": "コンテンツ分析パイプライン",
    },
    {
        "id": 3,
        "name": "LLMルーター (LLM-based Router)",
        "description": "LLMが質問のカテゴリ（技術/ビジネス/クリエイティブ）を判定し、専門エージェントに振り分ける",
        "graph_type": "llm_router",
        "use_case": "インテリジェントFAQシステム",
    },
    {
        "id": 4,
        "name": "ループ付き分岐 (Loop with Exit)",
        "description": "文章を改善するループ: 評価→改善→再評価を繰り返し、品質基準を満たしたら終了",
        "graph_type": "loop_with_condition",
        "use_case": "文章品質改善エージェント",
    },
]


_ls_project_info = None


def _get_ls_project_info() -> dict | None:
    """LangSmith の org_id と project_id をキャッシュして返す"""
    global _ls_project_info
    if _ls_project_info is not None:
        return _ls_project_info
    try:
        from langsmith import Client
        client = Client()
        project_name = os.environ.get("LANGCHAIN_PROJECT", "langchain-study")
        for p in client.list_projects():
            if p.name == project_name:
                _ls_project_info = {"org_id": str(p.tenant_id), "project_id": str(p.id)}
                return _ls_project_info
    except Exception:
        pass
    return None


def _langsmith_trace_url(run_id: str) -> str | None:
    """LangSmith のトレース URL を生成"""
    if os.environ.get("LANGCHAIN_TRACING_V2", "").lower() != "true":
        return None
    info = _get_ls_project_info()
    if not info:
        return None
    return (
        f"https://smith.langchain.com/o/{info['org_id']}/projects/p/{info['project_id']}"
        f"?peek={run_id}&peeked_trace={run_id}"
    )


def _build_response(response: dict, graph, trace: list[str], run_id: str) -> dict:
    """レスポンスに実行フロー Mermaid と LangSmith URL を追加"""
    response["executed_mermaid"] = get_mermaid_with_trace(graph, trace)
    url = _langsmith_trace_url(run_id)
    if url:
        response["langsmith_url"] = url
    return response


@router.get("/patterns")
def list_patterns():
    """全パターンの概要を返す"""
    return PATTERNS


@router.get("/patterns/{pattern_id}/graph")
async def get_graph(pattern_id: int):
    """指定パターンの Mermaid グラフを返す"""
    graph = GRAPHS.get(pattern_id)
    if not graph:
        return {"error": f"Pattern {pattern_id} not found"}
    return {"mermaid": get_mermaid(graph)}


@router.post("/patterns/{pattern_id}/run")
async def run_pattern(pattern_id: int, body: dict):
    """指定パターンのグラフを実行"""
    run_id = str(uuid.uuid4())
    run_name = RUN_NAMES.get(pattern_id, f"pattern{pattern_id}")
    tags = [f"pattern{pattern_id}"]

    if pattern_id == 1:
        result = graph1.invoke(
            {"input_text": body.get("input_text", ""), "trace": []},
            config={"run_id": run_id, "run_name": run_name, "tags": tags},
        )
        return _build_response({
            "input_text": result["input_text"],
            "sentiment": result["sentiment"],
            "reasoning": result["reasoning"],
            "response": result["response"],
            "trace": result["trace"],
        }, graph1, result["trace"], run_id)

    elif pattern_id == 2:
        result = graph2.invoke(
            {"input_text": body.get("input_text", ""), "trace": []},
            config={"run_id": run_id, "run_name": run_name, "tags": tags},
        )
        return _build_response({
            "input_text": result["input_text"],
            "summary": result.get("summary", ""),
            "keywords": result.get("keywords", ""),
            "translation": result.get("translation", ""),
            "final_report": result.get("final_report", ""),
            "trace": result["trace"],
        }, graph2, result["trace"], run_id)

    elif pattern_id == 3:
        result = graph3.invoke(
            {"question": body.get("question", ""), "trace": []},
            config={"run_id": run_id, "run_name": run_name, "tags": tags},
        )
        return _build_response({
            "question": result["question"],
            "category": result["category"],
            "reasoning": result["reasoning"],
            "expert_answer": result.get("expert_answer", ""),
            "formatted_answer": result.get("formatted_answer", ""),
            "trace": result["trace"],
        }, graph3, result["trace"], run_id)

    elif pattern_id == 4:
        result = graph4.invoke(
            {"topic": body.get("topic", ""), "max_iterations": body.get("max_iterations", 3), "trace": [], "iteration": 0},
            config={"run_id": run_id, "run_name": run_name, "tags": tags},
        )
        return _build_response({
            "topic": result["topic"],
            "draft": result["draft"],
            "score": result.get("score", 0),
            "evaluation": result.get("evaluation", ""),
            "reasoning": result.get("reasoning", ""),
            "iteration": result.get("iteration", 1),
            "final_output": result.get("final_output", ""),
            "trace": result["trace"],
        }, graph4, result["trace"], run_id)

    return {"error": f"Pattern {pattern_id} not found"}
