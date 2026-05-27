import ast
import asyncio
import json
import math
import operator
from collections.abc import AsyncGenerator

from llama_index.core import VectorStoreIndex
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool, QueryEngineTool

from app.core.chromadb import get_vector_store
from app.core.config import settings

# ---------------------------------------------------------------------------
# Safe calculator helpers
# ---------------------------------------------------------------------------

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_NAMES: dict = {
    "pi": math.pi,
    "e": math.e,
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
}


def _eval_node(node: ast.expr) -> float:
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op_fn = _SAFE_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_fn(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op_fn = _SAFE_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_fn(_eval_node(node.operand))
    if isinstance(node, ast.Name) and node.id in _SAFE_NAMES:
        return _SAFE_NAMES[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = _SAFE_NAMES.get(node.func.id)
        if fn is None:
            raise ValueError(f"Unsupported function: {node.func.id}")
        return fn(*[_eval_node(a) for a in node.args])
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def _calculate(expression: str) -> str:
    """Evaluate a safe mathematical expression and return the result as a string."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Agent service
# ---------------------------------------------------------------------------


class AgentService:
    def _build_rag_tool(self, index) -> QueryEngineTool:
        query_engine = index.as_query_engine(similarity_top_k=4)
        return QueryEngineTool.from_defaults(
            query_engine=query_engine,
            name="document_search",
            description=(
                "Search the uploaded documents for relevant information. "
                "Use this tool to answer questions about the document content."
            ),
        )

    def _build_calculator_tool(self) -> FunctionTool:
        return FunctionTool.from_defaults(
            fn=_calculate,
            name="calculator",
            description=(
                "Evaluate a mathematical expression. "
                "Supports +, -, *, /, ** and functions: sqrt, abs, round, pi, e. "
                "Example: '2 ** 10' or 'sqrt(144)'."
            ),
        )

    def _build_web_search_tool(self) -> FunctionTool | None:
        if not settings.tavily_api_key:
            return None

        def web_search(query: str) -> str:
            """Search the web for current information not in the documents."""
            try:
                from tavily import TavilyClient  # optional dependency
                client = TavilyClient(api_key=settings.tavily_api_key)
                result = client.search(query, max_results=3)
                snippets = [r.get("content", "") for r in result.get("results", [])]
                return "\n\n".join(snippets) or "No results found."
            except Exception as exc:
                return f"Web search error: {exc}"

        return FunctionTool.from_defaults(
            fn=web_search,
            name="web_search",
            description=(
                "Search the web for current information not in the uploaded documents. "
                "Use this for recent events, live data, or facts the documents don't cover."
            ),
        )

    def _build_agent(self, index) -> ReActAgent:
        tools = [
            self._build_rag_tool(index),
            self._build_calculator_tool(),
        ]
        web_tool = self._build_web_search_tool()
        if web_tool:
            tools.append(web_tool)
        return ReActAgent.from_tools(tools, verbose=False)

    async def stream_agent(self, question: str) -> AsyncGenerator[str, None]:
        vector_store = get_vector_store()
        index = await asyncio.to_thread(VectorStoreIndex.from_vector_store, vector_store)
        agent = self._build_agent(index)
        streaming_response = await asyncio.to_thread(agent.stream_chat, question)

        for token in streaming_response.response_gen:
            yield f"data: {json.dumps({'token': token})}\n\n"
            await asyncio.sleep(0)

        yield "data: [DONE]\n\n"