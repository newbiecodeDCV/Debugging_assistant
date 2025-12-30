"""Chat API routes."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from code_assistant.services import CodeAnalyzer

router = APIRouter()

# Service instance
_analyzer: CodeAnalyzer | None = None


def get_analyzer() -> CodeAnalyzer:
    """Get or create analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = CodeAnalyzer()
    return _analyzer


class ChatMessage(BaseModel):
    """A chat message."""

    role: str = Field(description="Role: 'user' or 'assistant'")
    content: str = Field(description="Message content")


class ChatRequest(BaseModel):
    """Request for chat endpoint."""

    message: str = Field(description="User's message")
    history: list[ChatMessage] | None = Field(
        default=None,
        description="Previous conversation history",
    )


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    response: str = Field(description="Assistant's response")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Interactive chat with the code assistant."""
    analyzer = get_analyzer()

    # Convert history to tuples
    history: list[tuple[str, str]] | None = None
    if request.history:
        history = []
        for i in range(0, len(request.history) - 1, 2):
            if i + 1 < len(request.history):
                user_msg = request.history[i]
                assistant_msg = request.history[i + 1]
                if user_msg.role == "user" and assistant_msg.role == "assistant":
                    history.append((user_msg.content, assistant_msg.content))

    response = await analyzer.chat(request.message, history)

    return ChatResponse(response=response)
