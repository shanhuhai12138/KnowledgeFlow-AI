# -*- coding: utf-8 -*-
"""graph 包 import 完整性回归测试。

背景：P1-1 拆分时 nodes.py 漏导入 get_llm_client，单测（不触发 LLM 调用）
未能发现，真实调用才暴露。本测试强制校验节点函数所需符号在模块作用域，
在 CI 即可拦截同类拆分回归。
"""
import inspect


def test_nodes_import_completeness():
    from graph import nodes

    required = ["get_llm_client", "sync_chat", "get_embedder", "build_context",
                "ensure_collection", "search", "get_settings", "QdrantClient"]
    for name in required:
        assert hasattr(nodes, name), f"nodes.py 缺少符号: {name}（拆分回归？）"


def test_nodes_public_functions_exist():
    from graph import nodes
    for fn in ["retrieve_node", "summarize_node", "classify_node",
               "report_gate_node", "report_node", "direct_answer_node"]:
        assert callable(getattr(nodes, fn)), f"节点函数缺失: {fn}"


def test_workflow_exports_api():
    from graph import workflow
    for fn in ["build_agent_graph", "start_agent_run", "approve_run", "_route_after_retrieve"]:
        assert callable(getattr(workflow, fn)), f"workflow 缺少: {fn}"


def test_shim_reexports_match():
    """agent_graph.py 垫片必须继续导出旧 API（routers 兼容）。"""
    from graph import agent_graph as shim
    for fn in ["build_agent_graph", "start_agent_run", "approve_run", "store", "AgentState"]:
        assert hasattr(shim, fn), f"垫片缺少旧导出: {fn}"


def test_graph_structure_stable():
    """六节点八边结构快照（与拆分等价性验证对应）。"""
    from graph.workflow import build_agent_graph
    g = build_agent_graph().get_graph()
    nodes_set = set(g.nodes.keys()) - {"__start__", "__end__"}
    assert nodes_set == {"retrieve", "summarize", "classify",
                         "report_gate", "report_node", "direct_answer"}
    edges = {(e.source, e.target) for e in g.edges}
    expected = {("__start__", "retrieve"), ("retrieve", "summarize"),
                ("retrieve", "direct_answer"), ("summarize", "classify"),
                ("classify", "report_gate"), ("report_gate", "report_node"),
                ("report_node", "__end__"), ("direct_answer", "__end__")}
    assert expected.issubset(edges), f"图结构漂移: {edges}"
