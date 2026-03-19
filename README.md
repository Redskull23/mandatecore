# MandateCore

MandateCore validates whether an AI-influenced banking decision can be executed under the current delegated authority, evidence, and policy thresholds.

This repo now includes a Streamlit workbench that reads the banking policy pack in `policies/` and records demo audit events for each validation run.

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

The original FastAPI entrypoint is still present. If you want to run that flow too, install the optional `api` dependencies and launch the app with your preferred ASGI server.
