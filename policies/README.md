# Banking Policy Pack

This policy pack gives MandateCore a concrete regulated-banking context.

It includes example runtime authority policies for:

- Wire transfers
- Fraud hold release
- Credit limit increase
- KYC / identity remediation

## Intent

These policies are designed to demonstrate how AI recommendations in a bank
can be constrained by runtime authority checks before execution.

Each policy includes:

- policy ID and version
- decision domain
- eligible actors
- allowed actions
- monetary thresholds
- evidence requirements
- escalation triggers
- hard-stop refusal triggers
- override rules
- audit expectations

## Suggested use in demo

1. AI makes a recommendation
2. MandateCore resolves the relevant policy
3. Runtime checks are performed
4. Outcome is returned: `ALLOW`, `ESCALATE`, or `REFUSE`

## Files

- `wire_transfers.yaml`
- `fraud_operations.yaml`
- `credit_decisions.yaml`
- `kyc_remediation.yaml`
- `policy_index.json`
