# AGENTS.md — Project Gamma

## Purpose of this file

This file gives coding agents (including Codex) durable project context, architecture decisions, current implementation status, and working conventions for Project Gamma.

**Important working style:** The owner is learning LangGraph and multi-agent design while building this project. Do not simply replace their work with a large finished implementation. Explain the reasoning, make incremental changes, preserve their learning opportunities, and review their code before proposing substantial rewrites.

---

# 1. Project overview

Project Gamma is a learning project evolving from a single-agent CSV analysis application into a multi-agent stock-market analysis system using LangGraph.

The intended multi-agent system will eventually accept natural-language stock-analysis requests, interpret the requested analysis, retrieve market/company data, delegate work to specialized agents, handle failures and stale data, and produce a final report.

The current implementation deliberately uses **mock/random data**. Do not represent mock outputs as real financial or market data.

Repository:
- GitHub: https://github.com/Vineet314/Project-Gamma
- The user develops locally on Windows, typically using PowerShell and a virtual environment.
- Earlier local project path: `C:\Users\Vineet\Desktop\trial`
- The user prefers committing and pushing code to GitHub rather than repeatedly pasting entire files into chat. When reviewing, inspect the checked-out repository and current working tree if available. Do not assume the remote branch is current or that a previously supplied commit is still HEAD.

## Primary learning goals

1. Understand LangGraph fundamentals through implementation.
2. Build a rule-based supervisor and specialized agents first.
3. Understand fan-out/fan-in and parallel execution.
4. Learn state updates, reducers, supersteps, streaming, checkpointing, interrupts, and error handling.
5. Later replace simple rule-based components with LLM-based interpretation/supervision.
6. Add real market/company data and tools only after the orchestration foundation is understood.
7. Keep the system testable and production-minded without overengineering the prototype.

---

# 2. Collaboration and teaching preferences

The user wants a guided, incremental learning experience.

- Explain *why* a design choice is made, not only what code to write.
- Prefer one small implementation task at a time.
- Ask the user to reason about behavior before revealing every answer when pedagogically useful.
- Review the user's implementation and point out specific issues.
- Avoid dumping a complete architecture or rewriting many files at once.
- Do not change the old `single_agent/` implementation unless explicitly requested.
- Preserve the existing architecture unless a concrete reason justifies changing it.
- Do not claim to have inspected GitHub code unless it was actually fetched or read.
- When repository access is available, use the local checkout/current files as the source of truth.
- When possible, work directly in the repo (e.g. via Codex) so the user does not need to paste code.
- Explain any edits and identify which files changed.
- Keep mock data clearly labelled as mock data.

---

# 3. Repository structure and intended responsibilities

The project evolved toward this structure:

```text
Project-Gamma/
├── .env
├── .gitignore
├── README.md
├── app.py
├── graph.py
├── state.py
├── agents/
│   ├── __init__.py
│   ├── supervisor.py
│   ├── financial.py
│   └── technical.py
├── tools/
│   ├── __init__.py
│   ├── financial_tools.py
│   ├── technical_tools.py
│   └── market_data_tools.py
└── single_agent/
    ├── agent.py
    ├── app.py
    ├── app_graph_v1.py
    ├── app_graph_v2.py
    ├── sales.csv
    └── ...
```

The exact current tree may differ; inspect it before editing.

### Responsibility boundaries

- `single_agent/`: original CSV-analysis learning project. Leave untouched unless asked.
- `state.py`: shared state and result schemas.
- `agents/supervisor.py`: decides which specialist agents should run.
- `agents/financial.py`: financial/fundamental analysis specialist.
- `agents/technical.py`: technical-analysis specialist.
- `tools/`: domain-specific tools, eventually bound to the appropriate agent(s).
- `graph.py`: LangGraph topology, nodes, edges, routing, compilation, and later checkpointer configuration.
- `app.py`: application entry point; accepts user input, classifies/validates the request, constructs initial state, invokes/streams the graph, and displays results.

Do not place graph construction in `app.py`; import the compiled graph from `graph.py`.

---

# 4. Single-agent project history and concepts learned

The user started with a single-agent CSV analysis application before beginning Project Gamma's multi-agent evolution.

Original local layout included:
- `single_agent/agent.py`
- `single_agent/app.py`
- `single_agent/app_graph_v1.py`
- `single_agent/app_graph_v2.py`
- `single_agent/sales.csv`
- `tools/csv_tools.py`
- `tools/py_tool.py`
- `.env`, `.gitignore`, `README.md`

The user explicitly requested that the original single-agent files not be modified while building the new multi-agent system.

Concepts already studied in the single-agent learning phase:

- LangGraph state schemas, commonly using `TypedDict`.
- Nodes, edges, `START`, and `END`.
- `StateGraph`, graph compilation, and invocation.
- Conditional edges and routing.
- Streaming and graph execution concepts.
- Tool definitions with `@tool`, binding tools to an LLM, tool calls, `ToolNode`, `tools_condition`, and custom tool execution.
- `ToolMessage` and tool-call result handling.
- Human-in-the-loop with `interrupt()` and `Command(resume=...)`.
- Important interrupt behavior: when resuming, the interrupted node may restart from its beginning, so code before the interrupt can execute again. Design side effects accordingly.
- Checkpointers, `InMemorySaver`, SQLite/Postgres checkpointers, `thread_id`, checkpoints, resume, and time-travel concepts.
- `add_messages`, reducers, and `Annotated`.
- TypedDict is a type declaration, not runtime validation and not a mechanism for automatically initializing default values.

Do not assume every concept is already mastered. Reinforce concepts in context as implementation progresses.

---

# 5. Multi-agent architecture decisions

## 5.1 What counts as an agent

An agent is more than an LLM call. It generally has a responsibility, instructions/context, decision-making or control logic, and optionally tools. An agent can be a simple Python function in an early prototype; it does not need an LLM or tools to be a useful graph node.

LangGraph is the orchestration layer. The LLM (when introduced) provides language understanding/reasoning; tools provide capabilities/data access; graph nodes and edges coordinate execution.

## 5.2 Supervisor design

Start with a deterministic, rule-based supervisor. It reads a structured `analysis_type` and returns the selected graph node names in `next_agents`.

Current intended mapping:

| `analysis_type` | `next_agents` |
|---|---|
| `fundamental` | `["financial_agent"]` |
| `technical` | `["technical_agent"]` |
| `full` | `["financial_agent", "technical_agent"]` |

The supervisor should not perform the financial or technical analysis. It selects and routes work.

Later, the rule-based supervisor can be replaced with an LLM-based supervisor, while preserving the same structured routing contract and graph orchestration.

## 5.3 Agent responsibilities and state ownership

- Financial agent owns `financial_analysis`.
- Technical agent owns `technical_analysis`.
- Supervisor owns `next_agents`.
- A future report/synthesis node will own `final_report`.

Each agent should return only the state update for its own key, not the entire shared state.

This ownership separation allows financial and technical nodes to execute in parallel without conflicting updates to the same state key.

A reducer is not required merely because two nodes execute in parallel. If they update different state keys, LangGraph can apply both updates. A reducer is needed when multiple updates to the *same* state channel must be combined in one superstep.

TypedDict nested dictionaries are replaced as whole values unless a reducer is deliberately configured; there is no automatic nested merge.

## 5.4 Parallel execution and supersteps

Financial and technical analysis are independent in the current design, so `full` analysis should fan out to both agents in parallel.

LangGraph uses superstep-style execution: nodes scheduled in the same superstep execute as a parallel set; updates are collected/applied before subsequent scheduled work proceeds. A downstream fan-in/report node can run after the relevant parallel branches complete.

Current graph has both specialist nodes pointing to `END`. When a reporter is added, change topology to:

```text
                 START
                   |
               Supervisor
                /      \
         Financial    Technical
                \      /
                Reporter
                   |
                  END
```

For a request that schedules only one specialist, the graph should still correctly proceed to the reporter after that selected branch. Verify conditional routing and fan-in behavior with the installed LangGraph version.

---

# 6. Current state schema and result contract

The user previously shared this state design (inspect current repository for exact latest version):

```python
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
    next_agents: list[str]

    # Agent outputs
    financial_analysis: AgentResult
    technical_analysis: AgentResult

    # Final output
    final_report: str
```

Possible future refinement discussed:
- Use `Literal` for allowed statuses, e.g. `pending`, `running`, `completed`, `failed`, and later `retrying`, `stale`, `completed_with_warnings`.
- TypedDict does not validate at runtime. Use explicit validation (or Pydantic/structured output where appropriate) at trust boundaries.
- Initialize fields explicitly when invoking the graph; TypedDict does not populate defaults.
- Consider optional/NotRequired fields only when the graph design genuinely needs partial inputs.

`AgentResult` contract:
- `status`: lifecycle status.
- `data`: optional result dictionary.
- `error`: optional error description (singular key; avoid mistakenly returning `errors`).
- `attempts`: number of actual attempts (the mock successful agents currently return `1`).

---

# 7. Current multi-agent implementation status

The latest user-reported working behavior (as of 2026-11-18) is:

- Rule-based query classification in `app.py`.
- Initial state construction.
- Rule-based supervisor.
- Mock financial and technical agents.
- `graph.py` with conditional routing.
- `graph.invoke(...)` successfully ran three test cases.

The user has successfully run these scenarios:

### Test 1: Fundamental

Input:
- Query: `financial analysis of TCS`
- Symbol: `TCS`

Observed:
- `analysis_type = "fundamental"`
- `next_agents = ["financial_agent"]`
- `financial_analysis.status = "completed"`
- `technical_analysis.status = "pending"`

### Test 2: Technical

Input:
- Query: `Technical indicators of INFY`
- Symbol: `INFY`

Observed:
- `analysis_type = "technical"`
- `next_agents = ["technical_agent"]`
- `technical_analysis.status = "completed"`
- `financial_analysis.status = "pending"`

### Test 3: Full

Input:
- Query: `Complete analysis of RELIANCE`
- Symbol: `RIL`

Observed:
- `analysis_type = "full"`
- `next_agents = ["financial_agent", "technical_agent"]`
- Both agent result statuses were `completed`.

The user has therefore demonstrated that the first multi-agent graph executes end-to-end and can schedule both specialists.

**Caveat:** the outputs are random mock values and are not financial advice or real stock data.

---

# 8. Current implementation details previously shared

These snippets are the user's last shared versions, not guaranteed to match the current GitHub HEAD. Always inspect current files before making edits.

## 8.1 Rule-based classifier in `app.py`

```python
def classify_query(user_query: str) -> str:
    word_list = set(user_query.lower().split())
    fundamental_keywords = {'fundamental', 'financial', 'ratio'}
    technical_keywords = {'technical', 'indicators', 'chart'}
    full_keywords = {'full', 'complete', 'comprehensive', 'thorough'}

    fundamental = bool(word_list & fundamental_keywords)
    technical = bool(word_list & technical_keywords)
    full = bool(word_list & full_keywords)

    if full or (fundamental and technical):
        return 'full'
    if fundamental:
        return 'fundamental'
    if technical:
        return 'technical'
    return 'unknown'
```

Limitations explicitly understood:
- It is a placeholder, not robust NLP.
- Exact token matching misses plurals/synonyms such as `ratios`, `charts`, and terms like `RSI`, `P/E`.
- It can classify `unknown`; app should ask for clarification and must not invoke the graph with an unknown type.
- A future LLM classifier should return structured, validated data (e.g. stock symbol, analysis type, confidence, needs_clarification), not unconstrained prose.
- The user's suggestion to use an LLM classifier is planned but not implemented.

## 8.2 Initial state builder

Previously shared:

```python
def build_initial_state(user_query: str, stock_symbol: str) -> StockAnalysisState:
    return {
        'stock_symbol': stock_symbol,
        'user_query': user_query,
        'analysis_type': classify_query(user_query),
        'next_agents': [],
        'financial_analysis': {
            'status': 'pending',
            'data': None,
            'error': None,
            'attempts': 0
        },
        'technical_analysis': {
            'status': 'pending',
            'data': None,
            'error': None,
            'attempts': 0
        },
        'final_report': ''
    }
```

The user initially extracted the ticker using a random token, which was identified as incorrect. The agreed placeholder approach was to ask the user for the symbol separately. Do not reintroduce random ticker extraction.

## 8.3 Supervisor

The user's last shared supervisor implementation had routing behavior like:

```python
def supervisor_agent(state: StockAnalysisState) -> dict:
    analysis_type = state["analysis_type"]

    if analysis_type == "fundamental":
        next_agents = ["financial_agent"]
    elif analysis_type == "technical":
        next_agents = ["technical_agent"]
    elif analysis_type == "full":
        next_agents = ["financial_agent", "technical_agent"]
    else:
        raise ValueError(f"Unsupported analysis type: {analysis_type}")

    return {"next_agents": next_agents}
```

The exact signature/import may differ in the repository. Ensure route strings match graph node names.

## 8.4 Mock financial agent

User previously shared a function named `financial` and then renamed it to `financial_agent`. The corrected behavior:
- accepts `fundamental` and `full`;
- generates random mock PE, market cap, industry PE, ROCE, profit;
- returns only `{"financial_analysis": AgentResult(...)}`;
- uses `error`, not `errors`;
- uses `attempts: 1`.

## 8.5 Mock technical agent

User previously shared:

```python
from typing import Any
import random

def technical_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    A mock agent that does technical analysis of a given stock.
    """

    assert state["analysis_type"] in ["technical", "full"]

    ticker = state["stock_symbol"]

    O = random.randint(100, 5000)
    H = O * (1 + random.uniform(0, 0.199))
    L = O * (1 - random.uniform(0, 0.199))
    C = random.uniform(L, H)
    OHLC = [O, H, L, C]
    RSI = random.uniform(10, 90)
    MA200 = C * random.uniform(0.75, 1.5)
    MA50 = C * random.uniform(0.75, 1.5)
    Vol = random.uniform(0.5, 100) * 1e5

    keys = ['OHLC', 'RSI', 'MA50', 'MA200', 'Volume']
    values = [OHLC, RSI, MA50, MA200, Vol]

    return {
        'technical_analysis': {
            "status": "completed",
            "data": {i: j for i, j in zip(keys, values)},
            "error": None,
            "attempts": 1
        }
    }
```

The OHLC percentage bug was corrected from `uniform(0, 19.9)` to `uniform(0, 0.199)`. The user was advised that `assert` is not ideal for runtime validation because Python optimization can disable assertions; explicit exceptions are preferable for production. `ticker` was extracted but not yet used in the mock implementation.

---

# 9. Current graph implementation

The user shared the following `graph.py` structure and confirmed successful execution:

```python
from langgraph.graph import StateGraph, START, END

from state import StockAnalysisState
from agents.supervisor import supervisor_agent
from agents.financial import financial_agent
from agents.technical import technical_agent

def should_continue(agent_state: StockAnalysisState) -> list[str]:
    return agent_state['next_agents']

builder = StateGraph(StockAnalysisState)
builder.add_node('supervisor_agent', supervisor_agent)
builder.add_node('financial_agent', financial_agent)
builder.add_node('technical_agent', technical_agent)

builder.add_edge(START, 'supervisor_agent')
builder.add_conditional_edges('supervisor_agent', should_continue)
builder.add_edge('financial_agent', END)
builder.add_edge('technical_agent', END)

graph = builder.compile()

config = {"configurable": {"thread_id": "multi-agent-1"}}
```

Important notes:
- The `add_conditional_edges` call returns route values that match node names.
- For a full request, `should_continue` returns both node names and LangGraph schedules both.
- Both agent nodes currently point to END.
- The user is using `graph.invoke(state, config=config)` and has successfully tested it.
- `thread_id` in config does not itself enable persistence. A checkpointer must be supplied to `compile()` for checkpointing.
- The user previously added a comment to `graph.py` about interrupts and incremental messages, but those features have not yet been implemented. Do not add them prematurely.

---

# 10. Next immediate lesson: streaming

The last assistant turn asked the user to predict what `graph.stream(..., stream_mode="updates")` returns for a full analysis.

The user's response to that question is not yet available in this context.

Next teaching steps:
1. Ask for or respond to the user's prediction.
2. Explain `updates` streaming: node-level state updates, generally separate node update events (the supervisor and then each agent) rather than a single combined agent update.
3. Have the user replace or supplement `invoke()` with:
   ```python
   for event in graph.stream(
       state,
       config=config,
       stream_mode="updates"
   ):
       print(event)
   ```
4. Observe output and explain the shape.
5. Compare with `stream_mode="values"` (full state snapshots after each graph step).
6. Discuss `messages` only when LLM nodes are introduced, as it streams LLM messages/tokens.
7. Do not overstate exact event ordering of parallel agents; both are scheduled in the same superstep, but observed output ordering can vary.

After streaming, the planned architecture roadmap includes:
- Add a Reporter/Synthesis node (fan-in) that consumes both specialist results.
- Test reporter behavior when only one agent was selected.
- Improve input classification and ticker extraction (eventually LLM structured output).
- Introduce real data and domain tools, using mock data until orchestration is stable.
- Add status/freshness/error semantics.
- Implement retry behavior for a failed agent only; retain successful sibling results.
- If retry still fails, continue with a partial report and explicitly mark the unavailable component.
- Learn `RetryPolicy`, error handling, idempotency, and checkpoint/pending-write behavior.
- Add checkpointer, `thread_id` persistence, interrupts/human approval as appropriate.
- Learn incremental messages/streaming.
- Later consider hierarchical/subgraph architecture, `Send`/map-reduce, async execution, runtime context/store, Functional API, observability/evaluation, and structured outputs.

---

# 11. Error handling decisions already discussed

The user has production pipeline experience in fraud detection (Kubeflow, Trino, Redis), and used that to reason about stale data, retries, and graceful degradation.

Agreed strategy:
- Retry only the failed agent, not all successful sibling agents.
- Preserve successful financial/technical/news results when another agent fails.
- If the retry also fails, continue with a partial report and explicitly mark the unavailable component.
- A `RetryPolicy` can retry qualifying exceptions at the node level.
- If a node catches the exception and returns a failed status, LangGraph's RetryPolicy will not see that exception; use a custom retry loop or route failures explicitly if returning state statuses.
- Checkpointing and pending writes can help preserve successful work from a failed superstep when resuming, depending on graph/checkpointer execution.
- Make external side effects idempotent where possible.
- A result's mere presence does not establish freshness or validity; represent status, timestamp/source, and staleness explicitly as the data layer matures.

---

# 12. Future design principles

- Prefer simple deterministic code for routing/validation and LLMs for ambiguous language understanding or synthesis.
- Validate LLM structured output before using it to schedule nodes.
- Keep data retrieval and analysis responsibilities distinct.
- Do not call live financial APIs until the user is ready; current agents are mocks.
- Avoid treating random metrics as valid market data.
- Keep state contracts explicit and consistent.
- Keep specialist agents independent where possible.
- Use fan-out/fan-in only where dependencies justify it.
- Do not add reducers preemptively; add them when multiple writers target the same state key and a merge policy is needed.
- Do not add persistence/interrupt complexity until the basic graph and streaming behavior are understood.
- Be careful with API keys and `.env`; never print or commit secrets.
- Do not modify `single_agent/` as part of multi-agent work unless the user explicitly requests it.

---

# 13. How Codex should start a new session

At the start of a new coding session:

1. Read this `AGENTS.md`.
2. Inspect the actual repository tree and current contents of:
   - `state.py`
   - `agents/supervisor.py`
   - `agents/financial.py`
   - `agents/technical.py`
   - `graph.py`
   - `app.py`
3. Check `git status`, current branch, and recent commit history.
4. Treat the current working tree as authoritative; this file is context, not proof that code still matches the snippets above.
5. Do not modify `single_agent/`.
6. Continue from the immediate next lesson: the user was asked to predict `stream_mode="updates"` output for a full analysis.
7. Explain the next step before making non-trivial edits, and keep changes small.
8. If the user asks for implementation directly, make the smallest coherent change, run relevant tests or a manual smoke test, and summarize changed files and results.
9. If something fails, report the actual error and what was/wasn't verified; never claim tests passed without running them.

## Definition of success for the current milestone

The basic multi-agent prototype is considered operational when:
- Fundamental requests schedule only the financial agent.
- Technical requests schedule only the technical agent.
- Full requests schedule both in parallel.
- Both agent updates appear in the final graph state.
- State keys and `AgentResult` contracts remain consistent.

This milestone has already been demonstrated by the user's reported `graph.invoke()` runs.
