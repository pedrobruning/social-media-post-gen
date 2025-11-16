"""LangGraph workflow definition for post generation.

This module constructs the agent workflow graph, defining how nodes
are connected and how state flows through the system.
"""

from typing import Literal

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from sqlalchemy import create_engine

from src.agent.nodes import (
    analyze_topic,
    apply_feedback,
    finalize,
    generate_image,
    generate_instagram,
    generate_linkedin,
    generate_wordpress,
    wait_for_approval,
)
from src.agent.state import PostGenerationState
from src.config.settings import settings


def should_regenerate(state: PostGenerationState) -> Literal["regenerate", "finalize"]:
    """Determine if content should be regenerated or finalized.
    
    This is a conditional edge function that routes based on approval status.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute
    """
    if state["approval_status"] == "approved":
        return "finalize"
    elif state["approval_status"] == "rejected":
        return "regenerate"
    else:
        # Still pending review
        return "wait"


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for post generation.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create PostgreSQL checkpointer for persistence
    engine = create_engine(settings.database_url)
    checkpointer = PostgresSaver(engine)
    
    # Create workflow graph
    workflow = StateGraph(PostGenerationState)
    
    # Add nodes
    workflow.add_node("analyze_topic", analyze_topic)
    workflow.add_node("generate_image", generate_image)
    workflow.add_node("generate_linkedin", generate_linkedin)
    workflow.add_node("generate_instagram", generate_instagram)
    workflow.add_node("generate_wordpress", generate_wordpress)
    workflow.add_node("wait_for_approval", wait_for_approval)
    workflow.add_node("apply_feedback", apply_feedback)
    workflow.add_node("finalize", finalize)
    
    # Define edges (workflow flow)
    # Start with topic analysis
    workflow.set_entry_point("analyze_topic")
    
    # After analysis, generate image
    workflow.add_edge("analyze_topic", "generate_image")
    
    # After image, generate all platform content in parallel
    # Note: LangGraph will execute these in parallel automatically
    workflow.add_edge("generate_image", "generate_linkedin")
    workflow.add_edge("generate_image", "generate_instagram")
    workflow.add_edge("generate_image", "generate_wordpress")
    
    # All platform generations converge to approval checkpoint
    workflow.add_edge("generate_linkedin", "wait_for_approval")
    workflow.add_edge("generate_instagram", "wait_for_approval")
    workflow.add_edge("generate_wordpress", "wait_for_approval")
    
    # Conditional routing after approval
    # TODO: Implement conditional edge based on approval_status
    # workflow.add_conditional_edges(
    #     "wait_for_approval",
    #     should_regenerate,
    #     {
    #         "regenerate": "apply_feedback",
    #         "finalize": "finalize",
    #         "wait": "wait_for_approval",  # Stay in wait state
    #     }
    # )
    
    # After applying feedback, regenerate content
    # TODO: Add conditional routing to specific platform nodes based on feedback
    workflow.add_edge("apply_feedback", "generate_linkedin")
    
    # After finalize, end workflow
    workflow.add_edge("finalize", END)
    
    # Compile workflow with checkpointer
    compiled_workflow = workflow.compile(checkpointer=checkpointer)
    
    return compiled_workflow


# Global workflow instance
workflow = create_workflow()

