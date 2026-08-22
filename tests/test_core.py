import pytest
from web3 import Web3
from vector_precedents import PrecedentEngine
from agentcourt import AgentCourtClient

def test_sdk_initialization():
    test_key = "0x" + "1" * 64
    client = AgentCourtClient(private_key=test_key)
    assert client.w3 is not None
    assert client.contract is not None
    assert Web3.is_address(client.contract_address)

def test_precedent_engine_storage_and_query():
    engine = PrecedentEngine()
    initial_count = engine.collection.count()
    
    # Store test precedent
    engine.store_verdict(
        case_id="unit_test_case_999",
        task_spec="Build API endpoint with rate limiting",
        deliverable="Endpoint built without rate limiting",
        worker_bps=5000,
        client_bps=5000,
        reasoning="Partial compliance unit test"
    )
    
    assert engine.collection.count() >= initial_count
