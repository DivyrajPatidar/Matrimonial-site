"""The master LangGraph state machine that wires nodes together."""
from langgraph.graph import StateGraph, END
from state.bot_state import BotState
from nodes.router_node import router_node
from nodes.registration_node import registration_node
from nodes.search_node import search_node
from nodes.update_node import update_node


def _route_after_router(state: BotState) -> str:
    """Decide which node runs next based on current_flow."""
    flow = state.get("current_flow", "welcome")
    if flow == "registration":
        return "registration"
    if flow == "search":
        return "search"
    if flow == "update":
        return "update"
    return END


def build_graph():
    g = StateGraph(BotState)
    g.add_node("router", router_node)
    g.add_node("registration", registration_node)
    g.add_node("search", search_node)
    g.add_node("update", update_node)

    g.set_entry_point("router")
    g.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "registration": "registration",
            "search": "search",
            "update": "update",
            END: END,
        },
    )
    # After each subflow we end (each call processes one user turn)
    g.add_edge("registration", END)
    g.add_edge("search", END)
    g.add_edge("update", END)

    return g.compile()


# Compile once at import time
graph = build_graph()
