# Clinical Trials AI MCP Server

> By [MEOK AI Labs](https://meok.ai) — Search, compare, and evaluate clinical trials with eligibility checking

## Installation

```bash
pip install clinical-trials-ai-mcp
```

## Usage

```bash
python server.py
```

## Tools

### `search_trials`
Search clinical trials by condition, drug, phase, status, or location.

**Parameters:**
- `condition` (str): Medical condition
- `drug` (str): Drug or intervention
- `phase` (str): Trial phase
- `status` (str): Trial status (recruiting, active, completed)
- `location` (str): Location filter

### `check_eligibility`
Evaluate whether a patient meets eligibility criteria for a specific trial.

**Parameters:**
- `trial_id` (str): Trial identifier (e.g., NCT00451932)
- `patient_age` (int): Patient age
- `patient_gender` (str): Patient gender
- `conditions` (str): Comma-separated patient conditions

### `get_trial_details`
Get comprehensive details for a specific clinical trial.

**Parameters:**
- `trial_id` (str): Trial identifier

### `compare_trials`
Compare multiple clinical trials side by side.

**Parameters:**
- `trial_ids` (str): Comma-separated trial IDs

### `get_trial_endpoints`
Get detailed primary and secondary endpoint information with study design.

**Parameters:**
- `trial_id` (str): Trial identifier

## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs
