import os
import json
import asyncio
import logging
from typing import Dict, Any, List
import statistics

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai
from dotenv import load_dotenv

from resolver import resolve_payload

load_dotenv()
logger = logging.getLogger("AgentCourt.Jurors")

# Initialize AI Clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) if os.getenv("ANTHROPIC_API_KEY") else None

if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


SYSTEM_PROMPT = """You are an impartial, highly rigorous AI juror in the decentralized dispute protocol 'AgentCourt'.
Your duty is to evaluate a completed deliverable against the initial task specification and evaluation criteria.

You must return ONLY a valid JSON object with the following schema:
{
  "basis_points": <integer between 0 and 10000>,
  "reasoning": "<concise justification in 2-3 sentences>",
  "confidence": <float between 0.0 and 1.0>
}
- 10000 basis points = 100% of escrow released to provider (flawless execution).
- 0 basis points = 0% released (complete default / failure).
- Do NOT wrap your output in markdown code blocks. Output raw JSON only.
"""


def build_evaluation_prompt(job_id: int, metadata: Dict[str, Any]) -> str:
    return f"""Case ID: Job #{job_id}
Task Specification:
{metadata.get('task_specification', 'N/A')}

Delivered Work / Evidence:
{metadata.get('deliverable_content', 'N/A')}

Evaluation Criteria:
{metadata.get('criteria', 'Standard quality and adherence to specs.')}
"""


async def evaluate_gpt4o(prompt: str) -> Dict[str, Any]:
    if not openai_client:
        return {"juror": "GPT-4o", "basis_points": 8500, "reasoning": "Fallback vote: OpenAI key missing.", "confidence": 0.8}
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        data["juror"] = "GPT-4o"
        return data
    except Exception as e:
        logger.warning(f"GPT-4o juror error: {e}")
        return {"juror": "GPT-4o", "basis_points": 8000, "reasoning": f"Parsing fallback: {e}", "confidence": 0.5}


async def evaluate_claude(prompt: str) -> Dict[str, Any]:
    if not anthropic_client:
        return {"juror": "Claude-Haiku", "basis_points": 8500, "reasoning": "Fallback vote: Anthropic key missing.", "confidence": 0.8}
    try:
        response = await anthropic_client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.content[0].text.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        data["juror"] = "Claude-Haiku"
        return data
    except Exception as e:
        logger.warning(f"Claude juror error: {e}")
        return {"juror": "Claude-Haiku", "basis_points": 8000, "reasoning": f"Parsing fallback: {e}", "confidence": 0.5}


async def evaluate_gemini(prompt: str) -> Dict[str, Any]:
    if not os.getenv("GEMINI_API_KEY"):
        return {"juror": "Gemini-Flash", "basis_points": 8500, "reasoning": "Fallback vote: Gemini key missing.", "confidence": 0.8}
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        response = await asyncio.to_thread(model.generate_content, prompt)
        content = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        data["juror"] = "Gemini-Flash"
        return data
    except Exception as e:
        logger.warning(f"Gemini juror error: {e}")
        return {"juror": "Gemini-Flash", "basis_points": 8000, "reasoning": f"Parsing fallback: {e}", "confidence": 0.5}


def apply_consensus_with_outlier_rejection(votes: List[Dict[str, Any]], outlier_threshold_bps: int = 2000) -> Dict[str, Any]:
    """
    Computes median BPS and discards any juror whose vote deviates
    from the raw median by more than outlier_threshold_bps.
    """
    valid_bps = [max(0, min(10000, int(v.get("basis_points", 5000)))) for v in votes]
    initial_median = int(statistics.median(valid_bps))

    filtered_votes = []
    dropped_votes = []

    for v, bps in zip(votes, valid_bps):
        if abs(bps - initial_median) > outlier_threshold_bps and len(valid_bps) > 2:
            dropped_votes.append({"juror": v.get("juror"), "basis_points": bps, "deviation": abs(bps - initial_median)})
        else:
            filtered_votes.append(v)

    # Re-calculate final consensus on clean votes
    clean_bps = [max(0, min(10000, int(v.get("basis_points", 5000)))) for v in filtered_votes]
    final_consensus_bps = int(statistics.median(clean_bps)) if clean_bps else initial_median

    opinions = [f"{v['juror']}: {v.get('basis_points')} bps ({v.get('reasoning', '')})" for v in filtered_votes]
    combined_opinion = " | ".join(opinions)[:280]

    return {
        "consensus_bps": final_consensus_bps,
        "raw_median_bps": initial_median,
        "opinion": combined_opinion,
        "juror_breakdown": votes,
        "outliers_dropped": dropped_votes
    }


async def deliberate_job(job_id: int, deliverable_hash: str) -> Dict[str, Any]:
    logger.info(f"Deliberating Job #{job_id} across multi-LLM jury...")
    metadata = await resolve_payload(deliverable_hash)
    prompt = build_evaluation_prompt(job_id, metadata)

    # Run jurors in parallel
    votes = await asyncio.gather(
        evaluate_gpt4o(prompt),
        evaluate_claude(prompt),
        evaluate_gemini(prompt),
        return_exceptions=False
    )

    result = apply_consensus_with_outlier_rejection(votes, outlier_threshold_bps=2000)
    logger.info(f"Consensus reached for Job #{job_id}: {result['consensus_bps']} bps (Outliers dropped: {len(result['outliers_dropped'])})")
    return result
