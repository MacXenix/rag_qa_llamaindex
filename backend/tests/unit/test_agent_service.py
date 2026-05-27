import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_service import AgentService, _calculate


class TestCalculator:
    def test_addition(self):
        assert _calculate("2 + 3") == "5.0"

    def test_subtraction(self):
        assert _calculate("10 - 4") == "6.0"

    def test_multiplication(self):
        assert _calculate("3 * 4") == "12.0"

    def test_division(self):
        assert _calculate("10 / 4") == "2.5"

    def test_power(self):
        assert _calculate("2 ** 10") == "1024.0"

    def test_sqrt(self):
        assert _calculate("sqrt(144)") == "12.0"

    def test_negative_number(self):
        assert _calculate("-5 + 3") == "-2.0"

    def test_invalid_expression_returns_error(self):
        result = _calculate("__import__('os')")
        assert result.startswith("Error:")

    def test_division_by_zero_returns_error(self):
        result = _calculate("1 / 0")
        assert result.startswith("Error:")

    def test_unsupported_name_returns_error(self):
        result = _calculate("x + 1")
        assert result.startswith("Error:")


class TestBuildTools:
    @pytest.fixture
    def service(self):
        return AgentService()

    def test_calculator_tool_name(self, service):
        tool = service._build_calculator_tool()
        assert tool.metadata.name == "calculator"

    def test_calculator_tool_works(self, service):
        tool = service._build_calculator_tool()
        result = tool("2 + 2")
        assert "4" in str(result)

    def test_rag_tool_name(self, service):
        mock_index = MagicMock()
        mock_index.as_query_engine.return_value = MagicMock()

        with patch("app.services.agent_service.QueryEngineTool") as mock_cls:
            mock_cls.from_defaults.return_value = MagicMock(
                metadata=MagicMock(name="document_search")
            )
            tool = service._build_rag_tool(mock_index)

        mock_cls.from_defaults.assert_called_once()
        mock_index.as_query_engine.assert_called_once_with(similarity_top_k=4)

    def test_web_search_tool_none_without_key(self, service):
        with patch("app.services.agent_service.settings") as mock_settings:
            mock_settings.tavily_api_key = ""
            result = service._build_web_search_tool()
        assert result is None

    def test_web_search_tool_returned_with_key(self, service):
        with patch("app.services.agent_service.settings") as mock_settings:
            mock_settings.tavily_api_key = "sk-test"
            tool = service._build_web_search_tool()
        assert tool is not None
        assert tool.metadata.name == "web_search"

    def test_build_agent_excludes_web_tool_without_key(self, service):
        mock_index = MagicMock()

        with patch.object(service, "_build_rag_tool", return_value=MagicMock()), \
             patch.object(service, "_build_calculator_tool", return_value=MagicMock()), \
             patch.object(service, "_build_web_search_tool", return_value=None), \
             patch("app.services.agent_service.ReActAgent") as mock_agent_cls:
            service._build_agent(mock_index)

        tools_passed = mock_agent_cls.from_tools.call_args[0][0]
        assert len(tools_passed) == 2

    def test_build_agent_includes_web_tool_with_key(self, service):
        mock_index = MagicMock()

        with patch.object(service, "_build_rag_tool", return_value=MagicMock()), \
             patch.object(service, "_build_calculator_tool", return_value=MagicMock()), \
             patch.object(service, "_build_web_search_tool", return_value=MagicMock()), \
             patch("app.services.agent_service.ReActAgent") as mock_agent_cls:
            service._build_agent(mock_index)

        tools_passed = mock_agent_cls.from_tools.call_args[0][0]
        assert len(tools_passed) == 3


class TestStreamAgent:
    @pytest.fixture
    def service(self):
        return AgentService()

    @pytest.mark.asyncio
    async def test_yields_token_events(self, service):
        mock_streaming = MagicMock()
        mock_streaming.response_gen = iter(["Hello", " world"])

        with patch("app.services.agent_service.get_vector_store"), \
             patch("asyncio.to_thread", new=AsyncMock(side_effect=[MagicMock(), mock_streaming])), \
             patch.object(service, "_build_agent", return_value=MagicMock()):
            events = [e async for e in service.stream_agent("What is 2+2?")]

        token_events = [e for e in events if '"token"' in e]
        assert len(token_events) == 2
        assert json.loads(token_events[0].removeprefix("data: "))["token"] == "Hello"

    @pytest.mark.asyncio
    async def test_yields_done_event(self, service):
        mock_streaming = MagicMock()
        mock_streaming.response_gen = iter([])

        with patch("app.services.agent_service.get_vector_store"), \
             patch("asyncio.to_thread", new=AsyncMock(side_effect=[MagicMock(), mock_streaming])), \
             patch.object(service, "_build_agent", return_value=MagicMock()):
            events = [e async for e in service.stream_agent("test")]

        assert any("[DONE]" in e for e in events)

    @pytest.mark.asyncio
    async def test_token_events_are_valid_sse(self, service):
        mock_streaming = MagicMock()
        mock_streaming.response_gen = iter(["token1"])

        with patch("app.services.agent_service.get_vector_store"), \
             patch("asyncio.to_thread", new=AsyncMock(side_effect=[MagicMock(), mock_streaming])), \
             patch.object(service, "_build_agent", return_value=MagicMock()):
            events = [e async for e in service.stream_agent("test")]

        for event in events:
            assert event.startswith("data: ")
            assert event.endswith("\n\n")