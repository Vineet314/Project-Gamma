from typing import Any
import random

def financial(state: dict[str, Any]) -> dict[str, Any]:
    """
    A mock agent that does financial analysis of a given stock.
    """

    assert state["analysis_type"] == "fundamental", 'Financial agent can only do fundamental analysis'
    
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
        "errors":None,
        "attempts":0}} # state update: give list of next agent/s to call