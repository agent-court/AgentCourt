import requests

class AgentCourtClient:
    def __init__(self, endpoint_url: str = "http://127.0.0.1:8000"):
        self.endpoint = endpoint_url.rstrip("/")

    def get_network_info(self):
        return requests.get(f"{self.endpoint}/").json()

    def create_escrow(self, worker_address: str, task_spec: str, amount_usd: float = 1.00, duration_seconds: int = 3600) -> int:
        payload = {
            "worker_address": worker_address,
            "task_spec": task_spec,
            "amount_usd": amount_usd,
            "duration_seconds": duration_seconds
        }
        res = requests.post(f"{self.endpoint}/tasks/create", json=payload).json()
        if "task_id" not in res:
            raise RuntimeError(f"Failed to create task: {res}")
        return res["task_id"]

    def submit_work(self, task_id: int, deliverable: str):
        payload = {"task_id": task_id, "deliverable": deliverable}
        return requests.post(f"{self.endpoint}/tasks/submit", json=payload).json()

    def arbitrate_and_settle(self, task_id: int, task_spec: str, deliverable: str):
        payload = {"task_id": task_id, "task_spec": task_spec, "deliverable": deliverable}
        return requests.post(f"{self.endpoint}/tasks/resolve", json=payload).json()

    def find_precedents(self, task_spec: str, deliverable: str, limit: int = 2):
        payload = {"task_spec": task_spec, "deliverable": deliverable, "limit": limit}
        return requests.post(f"{self.endpoint}/precedents/query", json=payload).json()
