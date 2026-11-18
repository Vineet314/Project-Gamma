from graph import StockAnalysisState
from typing import Any
import random

def financial_agent(state: StockAnalysisState) -> dict[str, Any]:
    """
    A mock agent that does financial analysis of a given stock.
    """

    assert state["analysis_type"] in ["fundamental", "full"], 'Financial agent can only do fundamental analysis'
    
    ticker = state["stock_symbol"]

    PE = len(ticker)*random.randint(4,8)
    MCAP = len(ticker)*random.randint(2,6)*10000
    IndPE = PE*random.randint(1,8)/4
    ROCE = random.uniform(1,15)
    Profit = random.choice([-1,1])*(random.uniform(0.25,0.75))*(MCAP/10)
    
    keys = ['PE', 'MCAP', 'Industry PE', 'ROCE', 'Profit']
    values = [PE,MCAP,IndPE,ROCE,Profit]

    return {'financial_analysis':{
        "status": "completed",
        "data": {i:j for i,j in zip(keys,values)},
        "error":None,
        "attempts":1}} 