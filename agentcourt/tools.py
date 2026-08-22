class AgentCourtTools:
    def __init__(self, client):
        self.client = client

    def get_escrow_tool(self):
        def hire_agent_with_escrow(contractor_address: str, task_spec: str, eth_amount: float) -> str:
            tx_hash, task_id = self.client.create_task(
                contractor=contractor_address,
                spec_uri=f"ipfs://{task_spec[:32]}",
                amount_eth=eth_amount
            )
            return f"Escrow Task #{task_id} successfully funded. TX: {tx_hash}"
        return hire_agent_with_escrow

    def get_dispute_tool(self):
        def dispute_agent_task(task_id: int, reason: str) -> str:
            tx_hash = self.client.raise_dispute(task_id=task_id, evidence_uri=f"ipfs://{reason[:32]}")
            return f"Dispute submitted for Task #{task_id}. Jury deliberation initiated. TX: {tx_hash}"
        return dispute_agent_task
