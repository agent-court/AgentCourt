import os
import re
import json
import asyncio
import logging
from typing import Dict, Any, List
import statistics

from resolver import resolve_payload

logger = logging.getLogger("AgentCourt.Jurors")


def parse_json_safely(raw_text: str) -> Dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def build_evaluation_prompt(job_id: int, payload: Dict[str, Any]) -> str:
    task_spec = payload.get("task_specification", "No specification provided.")
    deliverable = payload.get("deliverable_content", "No content provided.")
    criteria = payload.get("criteria", "Evaluate completeness and adherence to requirements.")

    return (
        f"You are a neutral decentralized court juror presiding over an on-chain escrow dispute in AgentCourt.\n\n"
        f"--- TASK SPECIFICATION ---\n"
        f"{task_spec}\n\n"
        f"--- DELIVERABLE SUBMITTED BY WORKER ---\n"
        f"{deliverable}\n\n"
        f"--- EVALUATION CRITERIA ---\n"
        f"{criteria}\n\n"
        f"--- INSTRUCTIONS ---\n"
        f"Assess how well the deliverable satisfies the task specification.\n"
        f"Assign a worker payout percentage expressed in basis points (0 to 10000 bps, where 10000 = 100% full payout, 5000 = 50% split, 0 = 0% full refund to client).\n"
        f"Provide concise reasoning (1-2 sentences max).\n\n"
        f"Respond ONLY with a raw JSON object formatted as:\n"
        f'{{"worker_bps": <integer 0-10000>, "reasoning": "<your concise justification>"}}'
    )


# 1. OpenAI Juror (gpt-4o)
async def call_openai_juror(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"model": "gpt-4o", "worker_bps": 5000, "reasoning": "Fallback: Key missing."}
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "model": "gpt-4o",
            "worker_bps": max(0, min(10000, int(data.get("worker_bps", 5000)))),
            "reasoning": data.get("reasoning", "")
        }
    except Exception as e:
        logger.error(f"OpenAI Juror Error: {e}")
        return {"model": "gpt-4o", "worker_bps": 5000, "reasoning": f"Error: {e}"}


# 2. Anthropic Juror (claude-haiku-4-5-20251001)
async def call_anthropic_juror(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"model": "claude-haiku-4-5", "worker_bps": 5000, "reasoning": "Fallback: Key missing."}
    
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        raw_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                raw_text += block.text
            elif isinstance(block, dict) and "text" in block:
                raw_text += block["text"]
                
        data = parse_json_safely(raw_text)
        return {
            "model": "claude-haiku-4-5",
            "worker_bps": max(0, min(10000, int(data.get("worker_bps", 5000)))),
            "reasoning": data.get("reasoning", "")
        }
    except Exception as e:
        logger.error(f"Anthropic Juror Error: {e}")
        return {"model": "claude-haiku-4-5", "worker_bps": 5000, "reasoning": f"Error: {e}"}


# 3. Google Gemini Juror (gemini-3.6-flash)
async def call_gemini_juror(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"model": "gemini-3.6-flash", "worker_bps": 5000, "reasoning": "Fallback: Key missing."}
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
        )
        data = parse_json_safely(response.text)
        return {
            "model": "gemini-3.6-flash",
            "worker_bps": max(0, min(10000, int(data.get("worker_bps", 5000)))),
            "reasoning": data.get("reasoning", "")
        }
    except Exception as e:
        logger.error(f"Gemini Juror Error: {e}")
        return {"model": "gemini-3.6-flash", "worker_bps": 5000, "reasoning": f"Error: {e}"}


# Aggregator
async def deliberate_job(job_id: int, deliverable_hash: str) -> Dict[str, Any]:
    logger.info(f"Resolving metadata for Job #{job_id} ({deliverable_hash[:10]}...)...")
    payload = await resolve_payload(deliverable_hash)
    
    prompt = build_evaluation_prompt(job_id, payload)
    logger.info(f"Dispatching Job #{job_id} with resolved spec to 3-juror quorum...")

    results: List[Dict[str, Any]] = await asyncio.gather(
        call_openai_juror(prompt),
        call_anthropic_juror(prompt),
        call_gemini_juror(prompt)
    )

    votes = [r["worker_bps"] for r in results]
    consensus_bps = int(statistics.median(votes))
    
    opinion_summary = f"Consensus ({consensus_bps} bps / {consensus_bps/100}%): " + " | ".join(
        [f"[{r['model']}: {r['worker_bps']} bps - {r['reasoning'][:35]}...]" for r in results]
    )

    return {
        "consensus_bps": consensus_bps,
        "opinion": opinion_summary[:500],
        "juror_breakdown": results
    }
