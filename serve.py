from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional, List
import os
import json
import requests


load_dotenv()


# Create MCP server
mcp = FastMCP("agent-studio")


# Get configuration from environment variables
def get_config():
    return {
        "host": os.environ.get("AGENT_STUDIO_DOMAIN", ""),
        "api_key": os.environ.get("CDSW_APIV2_KEY", "")
    }
    
CONFIG = get_config()

# Specify the mcp tools
@mcp.tool(
    description="List all of the current workflows available in an Agent Studio Instance"
)
def list_current_workflows() -> list[dict]:
    """
    List all of the current workflows available in an Agent Studio Instance.
    
    Returns:
        a list of all available workflows by their IDs and their names.
    """
    resp = requests.get(
        f"{CONFIG["host"]}/api/grpc/listWorkflows",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False
    )
    data = resp.json()
    workflows = data["workflows"]
    return [{"id": x["workflow_id"], "name": x["name"]} for x in workflows]


# Specify the mcp tools
@mcp.tool(
    description="Get information about a specific workflow in Agent Studio."
)
def get_workflow_information(id: str) -> dict:
    """
    Get information about a specific workflow in Agent Studio.
    
    Args:
        id: the workflow ID in question
    
    Returns:
        a JSON object describing this workflow
    """
    resp = requests.get(
        f"{CONFIG["host"]}/api/grpc/getWorkflow?workflow_id={id}",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False
    )
    data = resp.json()
    workflow = data["workflow"]
    return workflow


# Specify the mcp tools
@mcp.tool(
    description="Create a new workflow starting at a blank slate."
)
def create_workflow(name: str, description: str) -> dict:
    """
    Create a new workflow starting at a blank slate.
    
    Args:
        name: the name of the new workflow
        description: a decently sized description of the workflow, including what it will be used for
    
    Returns:
        the ID of the newly created workflow
    """
    resp = requests.post(
        f"{CONFIG["host"]}/api/grpc/addWorkflow",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
        json={
            "name": name,
            "description": description
        }
    )
    data = resp.json()
    return data


# Specify the mcp tools
@mcp.tool(
    description="Make a workflow conversational"
)
def make_workflow_conversational(workflow_id: str) -> str:
    """
    Make a workflow conversational

    Args:
        workflow_id (str): the workflow to enable conversational behavior on

    Returns:
        str: the Task ID of the conversational task
    """
    
    resp = requests.post(
        f"{CONFIG["host"]}/api/grpc/addTask",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
        json={
            "name": "Conversational Task",
            "add_crew_ai_task_request": {
                "description": "Respond to the user's message: {user_input}. Conversation history:\n{context}.",
                "expected_output": "Provide a response that aligns with the conversation history.",
                "assigned_agent_id": "",
            },
            "workflow_id": workflow_id,
            "template_id": '',
        }
    )
    data = resp.json()
    task_id = data["task_id"]
    
    # Get the workflow information so we can add the new agent.
    # this is ass backwords.
    workflow = get_workflow_information(workflow_id)

    # Update with the new agents
    resp = requests.post(
        f"{CONFIG["host"]}/api/grpc/updateWorkflow",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
        json={
            "workflow_id": workflow_id,
            "is_conversational": True,
            "crew_ai_workflow_metadata": {
                "agent_id": workflow["crew_ai_workflow_metadata"]["agent_id"],
                "manager_agent_id": workflow["crew_ai_workflow_metadata"]["manager_agent_id"],
                "task_id": [task_id],
                "process": workflow["crew_ai_workflow_metadata"]["process"],
                "manager_llm_model_provider_id": workflow["crew_ai_workflow_metadata"]["manager_llm_model_provider_id"]
            },
        }
    )
    data = resp.json()
    
    
    return task_id
    
    


@mcp.tool(
    description="Adds a new manager agent to a specified workflow."
)
def add_manager_agent_to_workflow(workflow_id: str, agent_name: str, agent_role: str, agent_backstory: str, agent_goal: str) -> dict:
    """
    Adds a new manager agent to a specified workflow.

    Args:
        workflow_id (str): _description_
        agent_name (str): _description_
        agent_role (str): Defines the manager agent’s function and expertise within the crew.
        agent_backstory (str): Provides context and personality to the manager agent, enriching interactions.
        agent_goal (str): The individual objective that guides the manager agent’s decision-making.

    Returns:
        dict: the ID of the new manager agent
    """
    
    # First, get the default model
    resp = requests.get(
        f"{CONFIG["host"]}/api/grpc/getStudioDefaultModel",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
    )
    data = resp.json()
    default_model_id = data["model_details"]["model_id"]
    
    
    resp = requests.post(
        f"{CONFIG["host"]}/api/grpc/addAgent",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
        json={
            "name": agent_name,
            "llm_provider_model_id": default_model_id,
            "tools_id": [],
            "crew_ai_agent_metadata": {
                "role": agent_role,
                "backstory": agent_backstory,
                "goal": agent_goal,
                "allow_delegation": False,
                "verbose": False,
                "cache": False, 
                "temperature": 0.1,
                "max_iter": 10
            },
            # "workflow_id": workflow_id,
            "tmp_agent_image_path": "",
            "tool_template_ids": []
        }
    )
    data = resp.json()
    agent_id = data["agent_id"]
    
    # Get the workflow information so we can add the new agent.
    # this is ass backwords.
    workflow = get_workflow_information(workflow_id)

    # Update with the new agents
    resp = requests.post(
        f"{CONFIG["host"]}/api/grpc/updateWorkflow",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
        json={
            "workflow_id": workflow_id,
            "crew_ai_workflow_metadata": {
                "agent_id": workflow["crew_ai_workflow_metadata"]["agent_id"],
                "manager_agent_id": agent_id,
                "task_id": workflow["crew_ai_workflow_metadata"]["task_id"],
                "process": "hierarchical",
                "manager_llm_model_provider_id": ""
            },
        }
    )
    data = resp.json()
    
    
    return agent_id




@mcp.tool(
    description="Adds a new agent to a specified workflow."
)
def add_agent_to_workflow(workflow_id: str, agent_name: str, agent_role: str, agent_backstory: str, agent_goal: str) -> dict:
    """
    Adds a new agent to a specified workflow.

    Args:
        workflow_id (str): _description_
        agent_name (str): _description_
        agent_role (str): Defines the agent’s function and expertise within the crew.
        agent_backstory (str): Provides context and personality to the agent, enriching interactions.
        agent_goal (str): 	The individual objective that guides the agent’s decision-making.

    Returns:
        dict: the ID of the new agent
    """
    
    # First, get the default model
    resp = requests.get(
        f"{CONFIG["host"]}/api/grpc/getStudioDefaultModel",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
    )
    data = resp.json()
    default_model_id = data["model_details"]["model_id"]
    
    
    resp = requests.post(
        f"{CONFIG["host"]}/api/grpc/addAgent",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
        json={
            "name": agent_name,
            "llm_provider_model_id": default_model_id,
            "tools_id": [],
            "crew_ai_agent_metadata": {
                "role": agent_role,
                "backstory": agent_backstory,
                "goal": agent_goal,
                "allow_delegation": False,
                "verbose": False,
                "cache": False, 
                "temperature": 0.1,
                "max_iter": 10
            },
            "workflow_id": workflow_id,
            "tmp_agent_image_path": "",
            "tool_template_ids": []
        }
    )
    data = resp.json()
    agent_id = data["agent_id"]
    
    
    # Get the workflow information so we can add the new agent.
    # this is ass backwords.
    workflow = get_workflow_information(workflow_id)
    
    agent_ids = workflow["crew_ai_workflow_metadata"]["agent_id"]
    agent_ids.append(agent_id)
    
    
    # Update with the new agents
    resp = requests.post(
        f"{CONFIG["host"]}/api/grpc/updateWorkflow",
        headers={
            'Authorization': f"Bearer {CONFIG["api_key"]}"
        },
        verify=False,
        json={
            "workflow_id": workflow_id,
            "crew_ai_workflow_metadata": {
                "agent_id": agent_ids,
                "task_id": workflow["crew_ai_workflow_metadata"]["task_id"],
                "manager_agent_id": workflow["crew_ai_workflow_metadata"]["manager_agent_id"],
                "process": workflow["crew_ai_workflow_metadata"]["process"],
                "manager_llm_model_provider_id": workflow["crew_ai_workflow_metadata"]["manager_llm_model_provider_id"]
            },
        }
    )
    data = resp.json()
    
    return agent_id




if __name__ == "__main__": 
    # Initialize and run the server
    mcp.run(transport='stdio')