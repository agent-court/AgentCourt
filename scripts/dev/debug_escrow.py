from agent import w3, escrow_contract, usdc_contract, ESCROW_ADDRESS

with open("treasury_address.txt") as f:
    treasury = w3.to_checksum_address(f.read().strip())

contract_usdc = usdc_contract.functions.balanceOf(ESCROW_ADDRESS).call()
treasury_usdc = usdc_contract.functions.balanceOf(treasury).call()
task_count = escrow_contract.functions.taskCount().call()

print("--- ESCROW CONTRACT STATE ---")
print(f"Contract Address : {ESCROW_ADDRESS}")
print(f"Contract USDC Bal: ${contract_usdc / 10**6:.4f} USDC")
print(f"Treasury Address : {treasury}")
print(f"Treasury USDC Bal: ${treasury_usdc / 10**6:.4f} USDC")
print(f"Total Tasks      : {task_count}")

if task_count > 0:
    print("\n--- RECENT TASK DATA ---")
    for i in range(1, min(task_count + 1, 5)):
        task = escrow_contract.functions.tasks(i).call()
        print(f"Task #{i}: Amount={task[3]/10**6} USDC, Status={task[6]} (0=Created, 1=Submitted, 2=Resolved)")
