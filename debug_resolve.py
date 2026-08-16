import traceback
import agent
import arbitrator
import precedent_db

spec = "Write a Python function `is_palindrome(s)` that returns True if a string is a palindrome."
worker_code = "def is_palindrome(s):\n    return s == s[::-1]"

print("1. Testing arbitrator.arbitrate_task...")
try:
    ruling = arbitrator.arbitrate_task(spec, worker_code)
    print("   ✅ Arbitrator succeeded:", ruling)
except Exception as e:
    print("   ❌ Arbitrator failed:")
    traceback.print_exc()
    exit(1)

print("\n2. Testing precedent_db.store_precedent...")
try:
    precedent_db.store_precedent(
        task_id=999,
        spec=spec,
        deliverable=worker_code,
        client_share=0,
        worker_share=100,
        opinion="Test opinion",
        category="debug_test"
    )
    print("   ✅ Precedent DB store succeeded!")
except Exception as e:
    print("   ❌ Precedent DB failed:")
    traceback.print_exc()

print("\n3. Testing resolveTask build & simulation...")
try:
    func = agent.escrow_contract.functions.resolveTask(9, 0)
    tx = agent.build_tx_with_gas(func, agent.CLIENT_ADDR, fallback_gas=350000)
    print("   ✅ Transaction build succeeded!")
except Exception as e:
    print("   ❌ Transaction build failed:")
    traceback.print_exc()
