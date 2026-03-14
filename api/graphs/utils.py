"""共通ユーティリティ: モデル初期化、グラフ可視化"""
import os
from langchain_anthropic import ChatAnthropic


def get_llm(temperature: float = 0.7) -> ChatAnthropic:
    """Anthropic Claude モデルを初期化"""
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=temperature,
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )


def get_mermaid(graph) -> str:
    """LangGraph のグラフから Mermaid 記法を取得"""
    return graph.get_graph().draw_mermaid()


def get_mermaid_with_trace(graph, trace: list[str]) -> str:
    """実行パスをハイライトした Mermaid を自前で組み立てる"""
    import re

    raw = graph.get_graph().draw_mermaid()

    # トレースからノード名を抽出（括弧付き情報を除去）
    executed = {re.sub(r"\(.*\)$", "", t) for t in trace}

    # 元の Mermaid からノード定義とエッジを解析
    # ノード: 元ID → (英数字ID, ラベル)
    id_map = {"__start__": "__start__", "__end__": "__end__"}
    nodes = []  # (new_id, label, is_executed)
    edges = []  # (src_orig, arrow, dst_orig)
    counter = 0

    for line in raw.split("\n"):
        # ノード定義行: \xxxx(ラベル)
        m = re.match(r"^\t([^\s(]+)\(([^)]+)\)", line)
        if m and not m.group(1).startswith("__"):
            orig_id = m.group(1)
            label = m.group(2)
            new_id = f"n{counter}"
            counter += 1
            id_map[orig_id] = new_id
            nodes.append((new_id, label, label in executed))
            continue

        # エッジ行: src --> dst or src -.-> dst or src ==> dst
        e = re.match(r"^\t([^\s;]+)\s+(-->|-\.->|==>)\s+([^\s;]+);", line)
        if e:
            edges.append((e.group(1), e.group(2), e.group(3)))

    # Mermaid を組み立て
    lines = ["graph TD;"]

    # START / END ノード
    lines.append('\t__start__(["__start__"]):::first')
    for new_id, label, is_exec in nodes:
        lines.append(f"\t{new_id}({label})")
    lines.append('\t__end__(["__end__"]):::last')

    # エッジ（実行パスは太線）
    executed_ids = {n[0] for n in nodes if n[2]}
    edge_index = 0
    executed_edge_indices = []
    for src_orig, arrow, dst_orig in edges:
        src = id_map.get(src_orig, src_orig)
        dst = id_map.get(dst_orig, dst_orig)
        src_is_exec = src in executed_ids or src == "__start__"
        dst_is_exec = dst in executed_ids or dst == "__end__"
        if src_is_exec and dst_is_exec:
            lines.append(f"\t{src} ==> {dst};")
            executed_edge_indices.append(edge_index)
        elif arrow == "-.->":
            lines.append(f"\t{src} -.-> {dst};")
        else:
            lines.append(f"\t{src} --> {dst};")
        edge_index += 1

    # ノードスタイル
    exec_ids = [n[0] for n in nodes if n[2]]
    inactive_ids = [n[0] for n in nodes if not n[2]]
    if exec_ids:
        for nid in exec_ids:
            lines.append(f"\tstyle {nid} fill:#065f46,stroke:#10b981,stroke-width:3px,color:#6ee7b7")
    if inactive_ids:
        for nid in inactive_ids:
            lines.append(f"\tstyle {nid} fill:#1e293b,stroke:#334155,stroke-width:1px,color:#64748b")

    # 実行パスのエッジを緑色に
    for idx in executed_edge_indices:
        lines.append(f"\tlinkStyle {idx} stroke:#10b981,stroke-width:3px")

    lines.append("\tclassDef first fill-opacity:0")
    lines.append("\tclassDef last fill:#bfb6fc")

    return "\n".join(lines)
