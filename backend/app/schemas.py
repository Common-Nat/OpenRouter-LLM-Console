from pydantic import BaseModel, Field
from typing import Optional, Literal

class ModelOut(BaseModel):
    id: str
    openrouter_id: str
    name: str
    context_length: Optional[int] = None
    pricing_prompt: Optional[float] = None
    pricing_completion: Optional[float] = None
    is_reasoning: bool = False

class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32768)
    openrouter_preset: Optional[str] = None

class ProfileOut(ProfileCreate):
    id: int

class SessionCreate(BaseModel):
    session_type: Literal["chat","code","documents","playground"] = "chat"
    title: Optional[str] = None
    profile_id: Optional[int] = None

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    profile_id: Optional[int] = None

class SessionOut(BaseModel):
    id: str
    session_type: str
    title: Optional[str] = None
    profile_id: Optional[int] = None
    created_at: str

class MessageCreate(BaseModel):
    session_id: str
    role: Literal["system","user","assistant","tool"]
    content: str = Field(min_length=1)

class MessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: str

class StreamRequest(BaseModel):
    session_id: str
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 2048


class UsageLogCreate(BaseModel):
    session_id: str
    model_id: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    profile_id: Optional[int] = None


class UsageLogOut(BaseModel):
    id: str
    session_id: str
    profile_id: Optional[int] = None
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    openrouter_id: Optional[str] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    created_at: str


class ModelUsageSummary(BaseModel):
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    openrouter_id: Optional[str] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class DocumentOut(BaseModel):
    id: str
    name: str
    size: int
    created_at: str


class DocumentQARequest(BaseModel):
    question: str = Field(min_length=1)
    model_id: str
    session_id: Optional[str] = None
    profile_id: Optional[int] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32768)


class MessageSearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Search query (supports FTS5 syntax)")
    session_id: Optional[str] = None
    session_type: Optional[Literal["chat","code","documents","playground"]] = None
    model_id: Optional[str] = None
    start_date: Optional[str] = Field(None, description="ISO format date (YYYY-MM-DD or full ISO datetime)")
    end_date: Optional[str] = Field(None, description="ISO format date (YYYY-MM-DD or full ISO datetime)")
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class MessageSearchResult(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: str
    session_type: str
    session_title: Optional[str] = None
    snippet: str  # Highlighted search snippet
    rank: float  # BM25 relevance score
