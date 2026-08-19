import os
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

from .vector_precedents import find_relevant_precedents

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def build_juror_prompt(task_spec: str, deliverable_evidence: str, precedents: List[Dict[str, Any]]) -> str:
    precedent_context = ""
    if precedents:
        precedent_context = "HISTORICAL CASE PRECEDENTS FOR GUIDANCE (STARE DECISIS):\n"
        for p in precedents:
            precedent_context += (
                f"- Case '{p.get('case_id', 'N/A')}' ({p.get('title', 'Precedent')}): Base split was {p.get('ruling_basis_points', 5000)} BPS "
                f"({int(p.get('ruling_basis_points', 5000))/100}%). Fact summary: {p.get('fact_summary', '')}\n"
            )
        precedent_context += "\n"

    return f"""You are an impartial algorithmic juror in the AgentCourt dispute resolution protocol on Base.
Your task is to evaluate the deliverable submitted against the formal task specification and determine a fair payout split in basis points (0 to 10000, where 10000 = 100% to worker, 0 = 100% refund to client).

{precedent_context}TASK SPECIFICATION:
{task_spec}

DELIVERABLE EVIDENCE / WORK AUDIT:
{deliverable_evidence}

Provide your ruling strictly in the following JSON format:
{{
  "worker_share_pct": <integer from 0 to 100>,
  "client_share_pct": <integer from 0 to 100>,
  "reasoning": "<concise 2-3 sentence legal/technical evaluation referencing criteria met/unmet and applicable precedent>"
}}
Only output valid JSON. No conversational preamble.
"""


def parse_verdict_json(text: str) -> Dict[str, Any]:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)


def deliberate_openai(prompt: str) -> Dict[str, Any]:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return parse_verdict_json(response.choices[0].message.content)


def deliberate_google(prompt: str) -> Dict[str, Any]:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return parse_verdict_json(response.text)


def arbitrate_task(task_spec: str, deliverable_evidence: str) -> Dict[str, Any]:
    precedents = find_relevant_precedents(task_spec, deliverable_evidence, top_k=2)
    prompt = build_juror_prompt(task_spec, deliverable_evidence, precedents)
    
    juror_rulings = []
    
    # Juror 1: OpenAI
    if OPENAI_API_KEY:
        try:
            r = deliberate_openai(prompt)
            juror_rulings.append(("OpenAI GPT-4o", r))
        except Exception as e:
            print(f"[!] Juror OpenAI deliberation failed: {e}")

    # Juror 2: Google Gemini
    if GOOGLE_API_KEY:
        try:
            r = deliberate_google(prompt)
            juror_rulings.append(("Google Gemini", r))
        except Exception as e:
            print(f"[!] Juror Google deliberation failed: {e}")

    if not juror_rulings:
        return {
            "worker_share_pct": 50,
            "client_share_pct": 50,
            "court_opinion": "Quorum unavailable; defaulted to 50/50 split.",
            "juror_opinions": [],
            "precedents": precedents
        }

    worker_votes = []
    for _, r in juror_rulings:
        pct = r.get("worker_share_pct", 50)
        if pct > 100:
            pct = round(pct / 100)
        worker_votes.append(pct)

    avg_worker_pct = round(sum(worker_votes) / len(worker_votes))
    avg_client_pct = 100 - avg_worker_pct

    opinions_summary = " | ".join([f"{name}: {r.get('reasoning', '')}" for name, r in juror_rulings])

    return {
        "worker_share_pct": avg_worker_pct,
        "client_share_pct": avg_client_pct,
        "court_opinion": opinions_summary,
        "juror_opinions": juror_rulings,
        "precedents": precedents
    }
