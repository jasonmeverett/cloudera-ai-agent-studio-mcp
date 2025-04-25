# Cloudera AI Agent Studio MCP Server

Agent Studio MCP Server is a lightweight Model Context Protocol (MCP) bridge that exposes your Agent Studio instance as a set of callable tools.
It lets Claude (or any other MCP-aware client) list, inspect, and build Agent Studio workflows on the fly.

## ✨ What it can do

| Tool | Description | Typical Usage |
|------|-------------|---------------|
| `list_current_workflows()` | Returns every workflow’s **ID** and **name** | Populate a UI drop-down of existing projects |
| `get_workflow_information(id)` | Fetch full JSON metadata for one workflow | Inspect tasks, agents, and process settings |
| `create_workflow(name, description)` | Spin up a brand-new blank workflow | Automate project scaffolding |
| `make_workflow_conversational(workflow_id)` | Adds a *Conversational Task* and flips `is_conversational` to `true` | Turn a static workflow into a chat-first experience |
| `add_manager_agent_to_workflow(workflow_id, …)` | Creates a **manager agent** and wires it in as the workflow’s supervisor | Hierarchical / delegated workflows |
| `add_agent_to_workflow(workflow_id, …)` | Adds any number of additional agents to a workflow | Expand the crew with domain specialists |



## 🖥 Integrating with Claude Desktop

Add the following block to your claude_desktop_config.json:


```
{
  "mcpServers": {
    "agent-studio": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/cloudera-ai-agent-studio-mcp",
        "run",
        "serve.py"
      ],
      "env": {
        "CDSW_APIV2_KEY": "YOUR-TOKEN-HERE",
        "AGENT_STUDIO_DOMAIN": "https://your-studio.CDSW_DOMAIN.cldr.work"
      }
    }
  }
}
```

