#!/usr/bin/env python3

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("clinical-trials-ai-mcp")
TRIALS = [
    {"id": "NCT001", "condition": "diabetes", "phase": "Phase II", "location": "London"},
    {"id": "NCT002", "condition": "hypertension", "phase": "Phase III", "location": "Manchester"},
]
@mcp.tool(name="search_trials")
async def search_trials(condition: str, phase: str = "", api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    matches = [t for t in TRIALS if condition.lower() in t["condition"] and (phase == "" or phase.lower() in t["phase"].lower())]
    return {"condition": condition, "matches": matches}
@mcp.tool(name="eligibility_check")
async def eligibility_check(age: int, conditions: list, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    eligible = age >= 18 and len(conditions) <= 3
    return {"eligible": eligible, "reason": "Age and comorbidity criteria met" if eligible else "Exclusion criteria may apply"}
if __name__ == "__main__":
    mcp.run()
