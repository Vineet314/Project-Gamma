from typing import TypedDict, Optional, Any


class AgentResult(TypedDict):
    status: str
    data: Optional[dict[str, Any]]
    error: Optional[str]
    attempts: int


class StockAnalysisState(TypedDict):

    # User input
    stock_symbol: str
    user_query: str

    # Supervisor
    analysis_type: str

    # Agent outputs
    financial_analysis: AgentResult
    technical_analysis: AgentResult

    # Final output
    final_report: str