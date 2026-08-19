import json
import os
import sys
from solcx import compile_standard, install_solc

SOLC_VERSION = "0.8.20"

def find_openzeppelin_dir():
    # Check current directory and parents for node_modules
    search_dirs = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.path.expanduser("~/AgentCourt"),
        os.path.expanduser("~/AgentCourt/agentcourt")
    ]
    
    for d in search_dirs:
        candidate = os.path.join(d, "node_modules", "@openzeppelin", "contracts")
        if os.path.isdir(candidate):
            return os.path.abspath(candidate)
            
    print("❌ Could not find node_modules/@openzeppelin/contracts automatically.")
    print("Running 'npm install @openzeppelin/contracts' in current folder...")
    os.system("npm install @openzeppelin/contracts")
    return os.path.abspath(os.path.join(os.getcwd(), "node_modules", "@openzeppelin", "contracts"))

def compile_v3():
    print(f"Ensuring solc v{SOLC_VERSION} is installed...")
    install_solc(SOLC_VERSION)

    contracts_dir = os.path.dirname(os.path.abspath(__file__))
    contract_file = os.path.join(contracts_dir, "AgentEscrowV3.sol")
    node_modules_oz = find_openzeppelin_dir()
    
    print(f"Found OpenZeppelin at: {node_modules_oz}")

    with open(contract_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    print("Compiling AgentEscrowV3.sol...")
    
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"AgentEscrowV3.sol": {"content": source_code}},
            "settings": {
                "optimizer": {"enabled": True, "runs": 200},
                "remappings": [
                    f"@openzeppelin/contracts/={node_modules_oz}/"
                ],
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                },
            },
        },
        solc_version=SOLC_VERSION,
        allow_paths=[node_modules_oz, contracts_dir, os.getcwd()],
    )

    contract_data = compiled_sol["contracts"]["AgentEscrowV3.sol"]["AgentEscrowV3"]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]

    output_abi_path = os.path.join(contracts_dir, "AgentEscrowV3_abi.json")
    output_bin_path = os.path.join(contracts_dir, "AgentEscrowV3_bytecode.bin")

    with open(output_abi_path, "w", encoding="utf-8") as f:
        json.dump(abi, f, indent=2)

    with open(output_bin_path, "w", encoding="utf-8") as f:
        f.write(bytecode)

    print(f"\n🎉 Compilation successful!")
    print(f"✅ ABI saved: {output_abi_path}")
    print(f"✅ Bytecode saved: {output_bin_path}")

if __name__ == "__main__":
    compile_v3()
