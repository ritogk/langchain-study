"""品質評価 (Evaluation) API"""
import os

from fastapi import APIRouter
from langsmith import Client

from graphs.pattern1_conditional import graph as graph1
from graphs.pattern3_llm_router import graph as graph3

router = APIRouter()

# LangSmith クライアント
_ls_client = None


def get_ls_client() -> Client | None:
    global _ls_client
    api_key = os.environ.get("LANGCHAIN_API_KEY")
    if not api_key:
        return None
    if _ls_client is None:
        _ls_client = Client()
    return _ls_client


USE_CASES = {
    "pattern1": {
        "name": "感情分析分岐テスト",
        "description": "カスタマーサポートの感情分析による振り分け精度を評価",
        "examples": [
            {"inputs": {"input_text": "この商品最高です！買ってよかった！"}, "outputs": {"expected_sentiment": "positive"}},
            {"inputs": {"input_text": "壊れてました。最悪です。返品します。"}, "outputs": {"expected_sentiment": "negative"}},
            {"inputs": {"input_text": "商品が届きました。サイズはMです。"}, "outputs": {"expected_sentiment": "neutral"}},
            {"inputs": {"input_text": "友達にプレゼントしたら、すごく喜んでくれました"}, "outputs": {"expected_sentiment": "positive"}},
            {"inputs": {"input_text": "3日経っても届かない。問い合わせても返事がない。"}, "outputs": {"expected_sentiment": "negative"}},
        ],
    },
    "pattern3": {
        "name": "LLMルーター分類テスト",
        "description": "質問カテゴリの分類精度を評価",
        "examples": [
            {"inputs": {"question": "Pythonでリスト内包表記の使い方を教えて"}, "outputs": {"expected_category": "tech"}},
            {"inputs": {"question": "スタートアップの資金調達方法について教えて"}, "outputs": {"expected_category": "business"}},
            {"inputs": {"question": "ロゴデザインの配色のコツを教えて"}, "outputs": {"expected_category": "creative"}},
            {"inputs": {"question": "KubernetesとDockerの違いは？"}, "outputs": {"expected_category": "tech"}},
            {"inputs": {"question": "効果的なブランディング戦略とは？"}, "outputs": {"expected_category": "business"}},
        ],
    },
}


@router.get("/eval/use-cases")
async def list_use_cases():
    """評価用ユースケース一覧"""
    return {
        key: {"name": v["name"], "description": v["description"], "example_count": len(v["examples"])}
        for key, v in USE_CASES.items()
    }


@router.post("/eval/create-dataset/{pattern_key}")
async def create_dataset(pattern_key: str):
    """LangSmith にデータセットを作成"""
    client = get_ls_client()
    if not client:
        return {"error": "LANGCHAIN_API_KEY が設定されていません。.env を確認してください。"}
    if pattern_key not in USE_CASES:
        return {"error": f"Unknown pattern: {pattern_key}"}

    use_case = USE_CASES[pattern_key]
    dataset_name = f"langchain-study-{pattern_key}"

    if client.has_dataset(dataset_name=dataset_name):
        existing = client.read_dataset(dataset_name=dataset_name)
        client.delete_dataset(dataset_id=existing.id)

    dataset = client.create_dataset(dataset_name=dataset_name, description=use_case["description"])
    client.create_examples(dataset_id=dataset.id, examples=use_case["examples"])

    return {"dataset_id": str(dataset.id), "dataset_name": dataset_name, "example_count": len(use_case["examples"])}


@router.post("/eval/run/{pattern_key}")
async def run_evaluation(pattern_key: str):
    """指定パターンの LangSmith 評価を実行"""
    client = get_ls_client()
    if not client:
        return {"error": "LANGCHAIN_API_KEY が設定されていません。.env を確認してください。"}
    if pattern_key not in USE_CASES:
        return {"error": f"Unknown pattern: {pattern_key}"}

    dataset_name = f"langchain-study-{pattern_key}"
    if not client.has_dataset(dataset_name=dataset_name):
        return {"error": f"データセット '{dataset_name}' が存在しません。先に create-dataset を実行してください。"}

    if pattern_key == "pattern1":
        def target(inputs: dict) -> dict:
            result = graph1.invoke(
                {"input_text": inputs["input_text"], "trace": []},
                config={"run_name": f"eval_{pattern_key}", "tags": ["evaluation", pattern_key]},
            )
            return {"sentiment": result["sentiment"], "reasoning": result["reasoning"]}

        def evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
            match = outputs.get("sentiment") == reference_outputs.get("expected_sentiment")
            return {"key": "sentiment_accuracy", "score": 1.0 if match else 0.0}

    elif pattern_key == "pattern3":
        def target(inputs: dict) -> dict:
            result = graph3.invoke(
                {"question": inputs["question"], "trace": []},
                config={"run_name": f"eval_{pattern_key}", "tags": ["evaluation", pattern_key]},
            )
            return {"category": result["category"], "reasoning": result["reasoning"]}

        def evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
            match = outputs.get("category") == reference_outputs.get("expected_category")
            return {"key": "category_accuracy", "score": 1.0 if match else 0.0}
    else:
        return {"error": f"パターン {pattern_key} の評価は未対応です"}

    results = client.evaluate(
        target, data=dataset_name, evaluators=[evaluator],
        experiment_prefix=f"langchain-study-eval-{pattern_key}", max_concurrency=2,
    )

    summary = []
    for r in results:
        summary.append({
            "inputs": r.get("example", {}).get("inputs", {}),
            "outputs": r.get("run", {}).get("outputs", {}),
            "scores": {
                er.key: er.score for er in (r.get("evaluation_results", {}).get("results", []))
            } if r.get("evaluation_results") else {},
        })

    return {"pattern": pattern_key, "dataset": dataset_name, "results": summary, "message": "評価結果は LangSmith UI でも確認できます"}


@router.post("/eval/run-local/{pattern_key}")
async def run_evaluation_local(pattern_key: str):
    """LangSmith なしでローカル評価を実行"""
    if pattern_key not in USE_CASES:
        return {"error": f"Unknown pattern: {pattern_key}"}

    use_case = USE_CASES[pattern_key]
    results = []

    for example in use_case["examples"]:
        inputs = example["inputs"]
        expected = example["outputs"]

        if pattern_key == "pattern1":
            result = graph1.invoke(
                {"input_text": inputs["input_text"], "trace": []},
                config={"run_name": f"local_eval_{pattern_key}", "tags": ["local_eval"]},
            )
            actual = result["sentiment"]
            expected_val = expected["expected_sentiment"]
            results.append({
                "input": inputs["input_text"], "expected": expected_val, "actual": actual,
                "reasoning": result.get("reasoning", ""), "match": actual == expected_val,
                "response": result.get("response", ""),
            })

        elif pattern_key == "pattern3":
            result = graph3.invoke(
                {"question": inputs["question"], "trace": []},
                config={"run_name": f"local_eval_{pattern_key}", "tags": ["local_eval"]},
            )
            actual = result["category"]
            expected_val = expected["expected_category"]
            results.append({
                "input": inputs["question"], "expected": expected_val, "actual": actual,
                "reasoning": result.get("reasoning", ""), "match": actual == expected_val,
            })

    accuracy = sum(1 for r in results if r["match"]) / len(results) if results else 0
    return {"pattern": pattern_key, "accuracy": accuracy, "total": len(results), "correct": sum(1 for r in results if r["match"]), "results": results}
