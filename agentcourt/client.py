import os
import re
import json
import ssl
import urllib.request
import urllib.error
from openai import OpenAI

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CONTEXT = ssl._create_unverified_context()

class AgentCourtClient:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    def _evaluate_openai(self, spec: str, evidence: str) -> dict:
        if not self.openai_key:
            return None
        try:
            client = OpenAI(api_key=self.openai_key)
            prompt = f"""
You are an objective AI Juror in AgentCourt evaluating an escrow dispute.
Task Spec: {spec}
Delivered Evidence: {evidence}

Determine the percentage (0 to 100) of the escrow funds that should be awarded to the Worker based on contract fulfillment.
Respond in this EXACT format:
RULING: <integer between 0 and 100>
OPINION: <1-2 sentences justifying your decision>
"""
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            text = res.choices[0].message.content.strip()
            match = re.search(r"RULING:\s*(\d+)", text)
            pct = int(match.group(1)) if match else 50
            opinion_match = re.search(r"OPINION:\s*(.*)", text, re.DOTALL)
            opinion = opinion_match.group(1).strip() if opinion_match else text
            return {"juror": "OpenAI GPT-4o", "worker_pct": pct, "opinion": opinion}
        except Exception as e:
            return {"juror": "OpenAI GPT-4o", "worker_pct": 50, "opinion": f"Evaluation error: {e}"}

    def _evaluate_anthropic(self, spec: str, evidence: str) -> dict:
        if not self.anthropic_key or not anthropic:
            return None
        
        models_to_try = [
            "claude-sonnet-4-6",
            "claude-3-5-sonnet-20241022",
            "claude-3-haiku-20240307"
        ]

        client = anthropic.Anthropic(api_key=self.anthropic_key)
        prompt = f"""
You are an objective AI Juror in AgentCourt evaluating an escrow dispute.
Task Spec: {spec}
Delivered Evidence: {evidence}

Determine the percentage (0 to 100) of the escrow funds that should be awarded to the Worker based on contract fulfillment.
Respond in this EXACT format:
RULING: <integer between 0 and 100>
OPINION: <1-2 sentences justifying your decision>
"""
        for model_id in models_to_try:
            try:
                msg = client.messages.create(
                    model=model_id,
                    max_tokens=256,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = msg.content[0].text.strip()
                match = re.search(r"RULING:\s*(\d+)", text)
                pct = int(match.group(1)) if match else 50
                opinion_match = re.search(r"OPINION:\s*(.*)", text, re.DOTALL)
                opinion = opinion_match.group(1).strip() if opinion_match else text
                return {"juror": f"Anthropic ({model_id})", "worker_pct": pct, "opinion": opinion}
            except Exception:
                continue

        return {"juror": "Anthropic Claude", "worker_pct": 50, "opinion": "No accessible Claude model found."}

    def _evaluate_gemini(self, spec: str, evidence: str) -> dict:
        if not self.gemini_key:
            return None
        
        models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        prompt = f"""
You are an objective AI Juror in AgentCourt evaluating an escrow dispute.
Task Spec: {spec}
Delivered Evidence: {evidence}

Determine the percentage (0 to 100) of the escrow funds that should be awarded to the Worker based on contract fulfillment.
Respond in this EXACT format:
RULING: <integer between 0 and 100>
OPINION: <1-2 sentences justifying your decision>
"""
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")

        for model_id in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={self.gemini_key}"
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=15) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()

                match = re.search(r"RULING:\s*(\d+)", text)
                pct = int(match.group(1)) if match else 50
                opinion_match = re.search(r"OPINION:\s*(.*)", text, re.DOTALL)
                opinion = opinion_match.group(1).strip() if opinion_match else text
                return {"juror": f"Google Gemini ({model_id})", "worker_pct": pct, "opinion": opinion}
            except Exception:
                continue

        return None

    def evaluate(self, spec: str, evidence: str) -> dict:
        evaluators = [self._evaluate_openai, self._evaluate_anthropic, self._evaluate_gemini]
        juror_results = []

        for eval_fn in evaluators:
            res = eval_fn(spec, evidence)
            if res:
                juror_results.append(res)

        if not juror_results:
            juror_results.append({"juror": "Fallback Juror", "worker_pct": 50, "opinion": "Default split."})

        total_worker_pct = sum(j["worker_pct"] for j in juror_results)
        consensus_worker = round(total_worker_pct / len(juror_results))
        consensus_client = 100 - consensus_worker

        formatted_opinions = " | ".join([f"{j['juror']}: {j['opinion']}" for j in juror_results])

        return {
            "worker_share_pct": consensus_worker,
            "client_share_pct": consensus_client,
            "court_opinion": formatted_opinions,
            "juror_count": len(juror_results)
        }
