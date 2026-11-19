from state import StockAnalysisState
from graph import graph, config

def classify_query(user_query: str) -> str:
    word_list = set(user_query.lower().split())
    fundamental_keywords = {'fundamental', 'financial','ratio'}
    technical_keywords = {'technical','indicators','chart'}
    full_keywords = {'full','complete','comprehensive','thorough'}

    fundamental = bool(word_list & fundamental_keywords)
    technical = bool(word_list & technical_keywords)
    full = bool(word_list & full_keywords)

    if full or (fundamental and technical): return 'full'
    if fundamental: return 'fundamental'
    if technical: return 'technical'
    return 'unknown'

def build_initial_state(user_query:str, stock_symbol:str) -> StockAnalysisState:
    return {
        'stock_symbol':stock_symbol,
        'user_query':user_query,
        'analysis_type':classify_query(user_query),
        'next_agents':[],
        'financial_analysis':{'status':'pending','data':None,'error':None,'attempts':0},
        'technical_analysis':{'status':'pending','data':None,'error':None,'attempts':0},
        'final_report':''
        }

def main():

    user_query = input('Human: ')
    while classify_query(user_query)=='unknown':
        print('Didn\'t quite catch that\n')
        user_query = input('Human: ')

    ticker = input('SYMBOL: ').upper().strip()
    while not bool(ticker):
        print('Please enter a valid ticker')
        ticker = input('SYMBOL: ').upper().strip()
        
    state = build_initial_state(user_query=user_query, stock_symbol=ticker)
    print("\n--- STREAMING UPDATES ---")                                                                                                                                                          
    for event in graph.stream(state, config=config, stream_mode="values"):                                                                                                                       
        print(event)                                                                                                                                                                              
        print("-" * 20)

if __name__=='__main__':
    main()