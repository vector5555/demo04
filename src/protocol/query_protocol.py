from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class QueryRequest:
    query_text: str
    context_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

@dataclass
class QueryResponse:
    sql: str
    result: Any
    context_id: str
    status: str