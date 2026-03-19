# MandateCore

MandateCore validates whether an AI-influenced banking decision can be executed under the current delegated authority, evidence, and policy thresholds.

This repo now includes a Streamlit workbench so you can explore the validator without standing up the API first.

## Run the Streamlit app

```bash
streamlit run streamlit_app.py
```

## What the Streamlit workbench includes

- Demo scenario presets from `demo/scenarios.py`
- Editable decision inputs for actor, action, amount, risk, and evidence
- Live authority context from the in-memory registry
- Validation results with `ALLOW`, `ESCALATE`, or `REFUSE` plus reasons

## Run the validator tests

```bash
python3 -m unittest discover -s test
```

## Optional API path

The original FastAPI entrypoint is still present. If you want to run that flow too, install the optional `api` dependencies and launch the app with your preferred ASGI server.
