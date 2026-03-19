URL = "http://127.0.0.1:8000/validate"

scenarios = [
    {
        "name": "Allow: low-risk wire under AI threshold",
        "payload": {
            "decision_id": "dec-1001",
            "actor_id": "ai_wire_agent",
            "actor_role": "ai_agent",
            "action": "approve_wire",
            "resource": "customer_account_8831",
            "amount": 5000,
            "risk_score": 0.22,
            "evidence_score": 0.93,
            "jurisdiction": "US",
            "business_unit": "consumer_banking",
            "override_requested": False,
        },
    },
    {
        "name": "Escalate: amount exceeds AI authority",
        "payload": {
            "decision_id": "dec-1002",
            "actor_id": "ai_wire_agent",
            "actor_role": "ai_agent",
            "action": "approve_wire",
            "resource": "customer_account_8831",
            "amount": 25000,
            "risk_score": 0.31,
            "evidence_score": 0.91,
            "jurisdiction": "US",
            "business_unit": "consumer_banking",
            "override_requested": False,
        },
    },
    {
        "name": "Escalate: evidence weak",
        "payload": {
            "decision_id": "dec-1003",
            "actor_id": "ai_wire_agent",
            "actor_role": "ai_agent",
            "action": "approve_wire",
            "resource": "customer_account_8831",
            "amount": 3000,
            "risk_score": 0.29,
            "evidence_score": 0.54,
            "jurisdiction": "US",
            "business_unit": "consumer_banking",
            "override_requested": False,
        },
    },
    {
        "name": "Refuse: hard stop risk threshold",
        "payload": {
            "decision_id": "dec-1004",
            "actor_id": "ai_wire_agent",
            "actor_role": "ai_agent",
            "action": "approve_wire",
            "resource": "customer_account_8831",
            "amount": 1000,
            "risk_score": 0.98,
            "evidence_score": 0.96,
            "jurisdiction": "US",
            "business_unit": "consumer_banking",
            "override_requested": False,
        },
    },
]

def main():
    import httpx

    with httpx.Client(timeout=10.0) as client:
        for scenario in scenarios:
            response = client.post(URL, json=scenario["payload"])
            print("\n" + "=" * 72)
            print(scenario["name"])
            print(response.json())

if __name__ == "__main__":
    main()
