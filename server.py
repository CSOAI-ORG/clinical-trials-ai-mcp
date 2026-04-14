#!/usr/bin/env python3
import json
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("clinical-trials-ai-mcp")
TRIALS = [
    {"id": "NCT001", "condition": "diabetes", "phase": "Phase II", "location": "London"},
    {"id": "NCT002", "condition": "hypertension", "phase": "Phase III", "location": "Manchester"},
]
@mcp.tool(name="search_trials")
async def search_trials(condition: str, phase: str = "") -> str:
    matches = [t for t in TRIALS if condition.lower() in t["condition"] and (phase == "" or phase.lower() in t["phase"].lower())]
    return json.dumps({"condition": condition, "matches": matches})
@mcp.tool(name="eligibility_check")
async def eligibility_check(age: int, conditions: list) -> str:
    eligible = age >= 18 and len(conditions) <= 3
    return json.dumps({"eligible": eligible, "reason": "Age and comorbidity criteria met" if eligible else "Exclusion criteria may apply"})
if __name__ == "__main__":
    mcp.run()
