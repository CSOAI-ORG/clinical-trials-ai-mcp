<div align="center">

# Clinical Trials Ai MCP

**MCP server for clinical trials ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-clinical-trials-ai-mcp)](https://pypi.org/project/meok-clinical-trials-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Clinical Trials Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `search_trials` | Search clinical trials by condition, drug, phase, status, or location. |
| `check_eligibility` | Evaluate whether a patient meets eligibility criteria for a specific trial. Cond |
| `get_trial_details` | Get comprehensive details for a specific clinical trial. |
| `compare_trials` | Compare multiple clinical trials side by side. Pass trial IDs as comma-separated |
| `get_trial_endpoints` | Get detailed primary and secondary endpoint information for a trial. |

## Installation

```bash
pip install meok-clinical-trials-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "clinical-trials-ai": {
      "command": "python",
      "args": ["-m", "meok_clinical_trials_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
