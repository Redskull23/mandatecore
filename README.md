# MandateCore
MandateCore helps determine whether an AI-influenced banking decision should actually go through—based on authority, available evidence, and policy constraints.

This repo includes a Streamlit workbench that loads a banking policy pack from policies/ and logs audit events for each validation run.

## Run the Streamlit app

```bash
streamlit run streamlit_app.py
```

## What the Streamlit workbench includes

- Demo scenario presets from `demo/scenarios.py` across wire, fraud, credit, and KYC flows
- YAML-backed policy resolution from `policies/policy_index.json` and the domain YAML files
- Generated policy context inputs based on required signals, rule conditions, overrides, and audit fields
- Live authority context from the demo certificate registry
- Validation results with `ALLOW`, `ESCALATE`, or `REFUSE` plus policy metadata and reasons
- An in-memory audit log with downloadable JSON export for demo sessions

## Policy pack

The demo policy pack lives in `policies/` and includes:

- `wire_transfers.yaml`
- `fraud_operations.yaml`
- `credit_decisions.yaml`
- `kyc_remediation.yaml`
- `policy_index.json`

## Run the validator tests

```bash
python3 -m unittest discover -s test
```

## Optional API path

There’s also a FastAPI entrypoint if you want to run this outside the Streamlit UI. Install the API dependencies and launch it with your preferred ASGI server.
