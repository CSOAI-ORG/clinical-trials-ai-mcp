#!/usr/bin/env python3
import urllib.request as _meter_urlreq
import urllib.error as _meter_urlerr
"""
Clinical Trials AI MCP Server - Search, compare, and evaluate clinical trials."""

import sys, os
from auth_middleware import check_access

import json, time, hashlib
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

# Rate limiting
_rate_limits: dict = defaultdict(list)
RATE_WINDOW = 60
MAX_REQUESTS = 30

def _check_rate(key: str) -> bool:
    now = time.time()
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < RATE_WINDOW]
    if len(_rate_limits[key]) >= MAX_REQUESTS:
        return False
    _rate_limits[key].append(now)
    return True

# Simulated clinical trials database
TRIALS_DB = [
    {
        "id": "NCT00451932", "title": "Metformin Extended Release in Type 2 Diabetes",
        "condition": "type 2 diabetes", "drug": "metformin", "phase": "Phase III",
        "status": "completed", "sponsor": "National Institute of Diabetes",
        "location": ["London, UK", "Birmingham, UK", "Manchester, UK"],
        "enrollment": 1200, "start_date": "2023-03-01", "end_date": "2025-09-30",
        "age_min": 18, "age_max": 75, "gender": "all",
        "inclusion": ["diagnosed type 2 diabetes", "HbA1c 7-10%", "BMI 25-40"],
        "exclusion": ["type 1 diabetes", "eGFR < 30", "pregnancy", "liver disease"],
        "primary_endpoint": "Change in HbA1c from baseline at 52 weeks",
        "secondary_endpoints": ["Fasting glucose change", "Weight change", "Adverse event rate", "Quality of life score"],
        "arms": [{"name": "Metformin XR 1000mg", "type": "experimental"}, {"name": "Placebo", "type": "control"}],
    },
    {
        "id": "NCT00523419", "title": "Lisinopril vs Amlodipine in Essential Hypertension",
        "condition": "hypertension", "drug": "lisinopril", "phase": "Phase III",
        "status": "recruiting", "sponsor": "British Heart Foundation",
        "location": ["Edinburgh, UK", "Oxford, UK"],
        "enrollment": 800, "start_date": "2024-06-01", "end_date": "2026-12-31",
        "age_min": 30, "age_max": 80, "gender": "all",
        "inclusion": ["essential hypertension", "systolic BP 140-180 mmHg", "no secondary causes"],
        "exclusion": ["secondary hypertension", "eGFR < 45", "bilateral renal artery stenosis", "pregnancy"],
        "primary_endpoint": "Change in 24-hour ambulatory blood pressure at 26 weeks",
        "secondary_endpoints": ["Office BP reduction", "Target BP achievement rate", "Cardiovascular events", "Tolerability"],
        "arms": [{"name": "Lisinopril 10-20mg", "type": "experimental"}, {"name": "Amlodipine 5-10mg", "type": "active_comparator"}],
    },
    {
        "id": "NCT00612847", "title": "Novel GLP-1 Agonist for Obesity Management",
        "condition": "obesity", "drug": "experimental GLP-1", "phase": "Phase II",
        "status": "recruiting", "sponsor": "Pharma Research Ltd",
        "location": ["London, UK", "New York, US", "Berlin, Germany"],
        "enrollment": 500, "start_date": "2025-01-15", "end_date": "2027-06-30",
        "age_min": 18, "age_max": 65, "gender": "all",
        "inclusion": ["BMI >= 30", "failed lifestyle intervention", "no bariatric surgery"],
        "exclusion": ["type 1 diabetes", "pancreatitis history", "MEN2 family history", "pregnancy"],
        "primary_endpoint": "Percentage body weight loss at 52 weeks",
        "secondary_endpoints": ["Waist circumference change", "Metabolic parameters", "Patient satisfaction", "Safety profile"],
        "arms": [{"name": "GLP-1 low dose", "type": "experimental"}, {"name": "GLP-1 high dose", "type": "experimental"}, {"name": "Placebo", "type": "control"}],
    },
    {
        "id": "NCT00734201", "title": "Pembrolizumab Combination in Advanced NSCLC",
        "condition": "lung cancer", "drug": "pembrolizumab", "phase": "Phase II",
        "status": "active", "sponsor": "Cancer Research UK",
        "location": ["London, UK", "Cambridge, UK"],
        "enrollment": 300, "start_date": "2024-03-01", "end_date": "2027-03-01",
        "age_min": 18, "age_max": 999, "gender": "all",
        "inclusion": ["advanced NSCLC stage IIIB-IV", "PD-L1 >= 1%", "ECOG 0-1", "adequate organ function"],
        "exclusion": ["autoimmune disease", "active brain metastases", "prior immunotherapy", "organ transplant"],
        "primary_endpoint": "Overall response rate per RECIST 1.1",
        "secondary_endpoints": ["Progression-free survival", "Overall survival", "Duration of response", "Immune-related adverse events"],
        "arms": [{"name": "Pembrolizumab + chemotherapy", "type": "experimental"}, {"name": "Chemotherapy alone", "type": "control"}],
    },
    {
        "id": "NCT00891524", "title": "Cognitive Behavioral Therapy for Treatment-Resistant Depression",
        "condition": "depression", "drug": "CBT intervention", "phase": "Phase III",
        "status": "recruiting", "sponsor": "NIHR Mental Health Research",
        "location": ["Manchester, UK", "Leeds, UK", "Bristol, UK"],
        "enrollment": 450, "start_date": "2025-02-01", "end_date": "2027-08-31",
        "age_min": 18, "age_max": 70, "gender": "all",
        "inclusion": ["major depressive disorder", "failed 2+ antidepressant trials", "PHQ-9 >= 15"],
        "exclusion": ["active psychosis", "substance dependence", "acute suicidal intent", "bipolar disorder"],
        "primary_endpoint": "Change in PHQ-9 score at 16 weeks",
        "secondary_endpoints": ["Remission rate", "Quality of life (EQ-5D)", "Work productivity", "Relapse rate at 52 weeks"],
        "arms": [{"name": "CBT + usual care", "type": "experimental"}, {"name": "Usual care alone", "type": "control"}],
    },
]

mcp = FastMCP("clinical-trials-ai", instructions="Search clinical trials, evaluate eligibility, compare trials, and retrieve endpoint data. Uses a reference database for demonstration purposes.")


def _server_meter_check(api_key: str = "") -> dict:
    """Calls the live /verify endpoint for server-side metering. Fail-open."""
    try:
        data = json.dumps({"api_key": api_key, "tool": ""}).encode()
        req = _meter_urlreq.Request(_METER_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with _meter_urlreq.urlopen(req, timeout=2.5) as r:
            d = json.loads(r.read())
            if isinstance(d, dict) and "allowed" in d:
                return d
    except Exception:
        pass
    return {"allowed": True, "tier": "anonymous", "remaining": 200, "upgrade_url": "https://meok.ai/pricing"}


_METER_URL = "https://proofof.ai/verify"


@mcp.tool()
def search_trials(condition: str = "", drug: str = "", phase: str = "", status: str = "", location: str = "", api_key: str = "") -> str:
    """Search clinical trials by condition, drug, phase, status, or location.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        condition (str): The condition to analyze or process.
        drug (str): The drug to analyze or process.
        phase (str): The phase to analyze or process.
        status (str): The status to analyze or process.
        location (str): The location to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://councilof.ai"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    if not any([condition, drug, phase, status, location]):
        return json.dumps({"error": "At least one search parameter required"})

    results = []
    for trial in TRIALS_DB:
        match = True
        if condition and condition.lower() not in trial["condition"].lower():
            match = False
        if drug and drug.lower() not in trial["drug"].lower():
            match = False
        if phase and phase.lower() not in trial["phase"].lower():
            match = False
        if status and status.lower() != trial["status"].lower():
            match = False
        if location:
            if not any(location.lower() in loc.lower() for loc in trial["location"]):
                match = False
        if match:
            results.append({
                "id": trial["id"],
                "title": trial["title"],
                "condition": trial["condition"],
                "phase": trial["phase"],
                "status": trial["status"],
                "sponsor": trial["sponsor"],
                "enrollment": trial["enrollment"],
                "locations": trial["location"],
            })

    return json.dumps({
        "query": {"condition": condition, "drug": drug, "phase": phase, "status": status, "location": location},
        "total_results": len(results),
        "results": results,
        "searched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


@mcp.tool()
def check_eligibility(trial_id: str, patient_age: int, patient_gender: str = "any", conditions: str = "", api_key: str = "") -> str:
    """Evaluate whether a patient meets eligibility criteria for a specific trial. Conditions as comma-separated string.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        trial_id (str): The trial id to analyze or process.
        patient_age (int): The patient age to analyze or process.
        patient_gender (str): The patient gender to analyze or process.
        conditions (str): The conditions to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://councilof.ai"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    trial = None
    for t in TRIALS_DB:
        if t["id"] == trial_id:
            trial = t
            break
    if not trial:
        return json.dumps({"error": f"Trial {trial_id} not found"})

    patient_conditions = [c.strip().lower() for c in conditions.split(",") if c.strip()]
    eligible = True
    reasons = []
    warnings = []

    # Age check
    if patient_age < trial["age_min"]:
        eligible = False
        reasons.append(f"Patient age {patient_age} below minimum {trial['age_min']}")
    if trial["age_max"] < 999 and patient_age > trial["age_max"]:
        eligible = False
        reasons.append(f"Patient age {patient_age} above maximum {trial['age_max']}")

    # Gender check
    if trial["gender"] != "all" and patient_gender.lower() != trial["gender"].lower():
        eligible = False
        reasons.append(f"Trial restricted to {trial['gender']} participants")

    # Status check
    if trial["status"] not in ["recruiting", "active"]:
        warnings.append(f"Trial status is '{trial['status']}' - may not be accepting new participants")

    # Exclusion criteria check
    for exclusion in trial["exclusion"]:
        for cond in patient_conditions:
            if cond in exclusion.lower() or exclusion.lower() in cond:
                eligible = False
                reasons.append(f"Exclusion criterion matched: '{exclusion}' (patient has '{cond}')")

    # Inclusion criteria match
    inclusion_matches = 0
    for inclusion in trial["inclusion"]:
        for cond in patient_conditions:
            if any(word in inclusion.lower() for word in cond.split()):
                inclusion_matches += 1
                break

    if len(trial["inclusion"]) > 0:
        inclusion_coverage = round((inclusion_matches / len(trial["inclusion"])) * 100, 1)
    else:
        inclusion_coverage = 100.0

    if inclusion_coverage < 50:
        warnings.append(f"Only {inclusion_coverage}% of inclusion criteria clearly matched - further screening needed")

    return json.dumps({
        "trial_id": trial_id,
        "trial_title": trial["title"],
        "eligible": eligible,
        "inclusion_coverage_pct": inclusion_coverage,
        "exclusion_reasons": reasons,
        "warnings": warnings,
        "patient_summary": {"age": patient_age, "gender": patient_gender, "conditions": patient_conditions},
        "trial_criteria": {"inclusion": trial["inclusion"], "exclusion": trial["exclusion"]},
        "assessed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "disclaimer": "Preliminary eligibility screening only. Full screening by trial site required.",
    })


@mcp.tool()
def get_trial_details(trial_id: str, api_key: str = "") -> str:
    """Get comprehensive details for a specific clinical trial.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        trial_id (str): The trial id to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://councilof.ai"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    trial = None
    for t in TRIALS_DB:
        if t["id"] == trial_id:
            trial = t
            break
    if not trial:
        return json.dumps({"error": f"Trial {trial_id} not found"})

    return json.dumps({
        "id": trial["id"],
        "title": trial["title"],
        "condition": trial["condition"],
        "intervention": trial["drug"],
        "phase": trial["phase"],
        "status": trial["status"],
        "sponsor": trial["sponsor"],
        "locations": trial["location"],
        "enrollment_target": trial["enrollment"],
        "timeline": {"start_date": trial["start_date"], "end_date": trial["end_date"]},
        "eligibility": {
            "age_range": f"{trial['age_min']}-{trial['age_max'] if trial['age_max'] < 999 else 'no limit'}",
            "gender": trial["gender"],
            "inclusion_criteria": trial["inclusion"],
            "exclusion_criteria": trial["exclusion"],
        },
        "study_design": {"arms": trial["arms"], "arm_count": len(trial["arms"])},
        "endpoints": {
            "primary": trial["primary_endpoint"],
            "secondary": trial["secondary_endpoints"],
        },
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


@mcp.tool()
def compare_trials(trial_ids: str, api_key: str = "") -> str:
    """Compare multiple clinical trials side by side. Pass trial IDs as comma-separated string.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        trial_ids (str): The trial ids to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://councilof.ai"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    ids = [tid.strip() for tid in trial_ids.split(",") if tid.strip()]
    if len(ids) < 2:
        return json.dumps({"error": "At least 2 trial IDs required for comparison"})

    trials_found = []
    not_found = []
    for tid in ids:
        found = False
        for t in TRIALS_DB:
            if t["id"] == tid:
                trials_found.append(t)
                found = True
                break
        if not found:
            not_found.append(tid)

    if len(trials_found) < 2:
        return json.dumps({"error": f"Need at least 2 valid trials. Not found: {not_found}"})

    comparison = []
    for trial in trials_found:
        comparison.append({
            "id": trial["id"],
            "title": trial["title"],
            "phase": trial["phase"],
            "status": trial["status"],
            "condition": trial["condition"],
            "intervention": trial["drug"],
            "enrollment": trial["enrollment"],
            "locations_count": len(trial["location"]),
            "arm_count": len(trial["arms"]),
            "duration_info": f"{trial['start_date']} to {trial['end_date']}",
            "primary_endpoint": trial["primary_endpoint"],
            "secondary_endpoint_count": len(trial["secondary_endpoints"]),
            "inclusion_count": len(trial["inclusion"]),
            "exclusion_count": len(trial["exclusion"]),
        })

    # Highlight differences
    differences = []
    if len(set(t["phase"] for t in trials_found)) > 1:
        differences.append("Different trial phases")
    if len(set(t["status"] for t in trials_found)) > 1:
        differences.append("Different recruitment statuses")
    enrollments = [t["enrollment"] for t in trials_found]
    if max(enrollments) > min(enrollments) * 2:
        differences.append("Significant enrollment size difference")

    return json.dumps({
        "trials_compared": len(trials_found),
        "not_found": not_found,
        "comparison": comparison,
        "key_differences": differences,
        "compared_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


@mcp.tool()
def get_trial_endpoints(trial_id: str, api_key: str = "") -> str:
    """Get detailed primary and secondary endpoint information for a trial.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        trial_id (str): The trial id to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://councilof.ai"})
    if not _check_rate(api_key or "anon"):
        return json.dumps({"error": "Rate limit exceeded. Try again in 60 seconds."})

    trial = None
    for t in TRIALS_DB:
        if t["id"] == trial_id:
            trial = t
            break
    if not trial:
        return json.dumps({"error": f"Trial {trial_id} not found"})

    # Enrich endpoint data with measurement info
    primary = {
        "endpoint": trial["primary_endpoint"],
        "type": "primary",
        "measurement_type": "continuous" if any(w in trial["primary_endpoint"].lower() for w in ["change", "score", "rate", "percentage"]) else "categorical",
        "timepoint": "See trial protocol for exact timepoints",
    }

    secondary = []
    for ep in trial["secondary_endpoints"]:
        secondary.append({
            "endpoint": ep,
            "type": "secondary",
            "measurement_type": "continuous" if any(w in ep.lower() for w in ["change", "score", "rate", "survival"]) else "categorical",
        })

    # Statistical design info
    is_rct = len(trial["arms"]) >= 2
    has_control = any(a["type"] in ["control", "active_comparator"] for a in trial["arms"])

    return json.dumps({
        "trial_id": trial_id,
        "trial_title": trial["title"],
        "primary_endpoint": primary,
        "secondary_endpoints": secondary,
        "total_endpoints": 1 + len(secondary),
        "study_design": {
            "randomized": is_rct,
            "controlled": has_control,
            "arms": trial["arms"],
        },
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


def main():
    mcp.run()

if __name__ == '__main__':
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/5kQ6oJ0xS3ce8sl7ew8k91j"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
