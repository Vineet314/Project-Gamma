from typing import TypedDict


class StockAnalysisState(TypedDict):

    # User input
    stock_symbol: str
    user_query: str

    # Supervisor
    analysis_type: str

    # Agent outputs
    financial_analysis: dict
    technical_analysis: dict

    # Final output
    final_report: str