import time
from agent import (
    create_task_usdc,
    submit_task,
    ai_evaluate_and_resolve,
    WORKER_ADDR,
    ESCROW_ADDRESS,
    w3
)

# Define our 3 adversarial test cases
TEST_CASES = [
    {
        "name": "Case A: Perfect Delivery (Expects ~100% Worker)",
        "spec": "Write a Python function `format_currency(amount)` that returns a number formatted as USD currency string (e.g., 1234.5 -> '$1,234.50').",
        "deliverable": "def format_currency(amount):\n    return f'${amount:,.2f}'",
        "amount_usd": 1.00
    },
    {
        "name": "Case B: Partial Compliance / Edge Case Bug (Expects Split Ruling)",
        "spec": "Write a Python function `safe_divide(a, b)` that returns a/b, or None if b is 0. Include type hinting.",
        "deliverable": "def safe_divide(a, b):\n    # Missed type annotations and returns 0 instead of None\n    if b == 0:\n        return 0\n    return a / b",
        "amount_usd": 1.00
    },
    {
        "name": "Case C: Total Breach / Bad-Faith Junk (Expects 100% Client Refund)",
        "spec": "Write a Python function `parse_json_payload(raw_str)` that parses JSON string safely.",
        "deliverable": "console.log('Hello world, I do not know Python');",
        "amount_usd": 1.00
    }
]

def run_adversarial_suite():
    print("=" * 70)
    print("⚖️  AGENTCOURT ADVERSARIAL DISPUTE SIMULATION SUITE")
    print(f"🔗 Target Escrow Contract: {ESCROW_ADDRESS}")
    print("=" * 70)

    for idx, case in enumerate(TEST_CASES, start=1):
        print(f"\n[{idx}/3] 📋 RUNNING: {case['name']}")
        print(f"     Task Spec    : {case['spec']}")
        print(f"     Deliverable  :\n{case['deliverable']}\n")

        # 1. Create on-chain task with $1.00 USDC
        task_id = create_task_usdc(
            worker_addr=WORKER_ADDR,
            details_hash=case["spec"],
            amount_usd=case["amount_usd"],
            duration_seconds=3600
        )
        time.sleep(2)

        # 2. Worker submits deliverable
        submit_task(task_id, case["deliverable"])
        time.sleep(2)

        # 3. AI Court Arbitrator deliberates and executes on-chain settlement
        ai_evaluate_and_resolve(task_id, case["spec"], case["deliverable"])
        
        print(f"✅ Finished {case['name']}")
        print("-" * 70)
        time.sleep(3)

    print("\n🎉 ALL 3 ADVERSARIAL DISPUTE SCENARIOS COMPLETED ON BASE SEPOLIA!")

if __name__ == "__main__":
    if w3.is_connected():
        run_adversarial_suite()
    else:
        print("❌ Could not connect to Base Sepolia RPC.")