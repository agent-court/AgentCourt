import os
import re
import json
import asyncio
import logging
from typing import Dict, Any, List
import statistics

logger = logging.getLogger("AgentCourt.Jurors")


def parse_json_safely(raw_text: str) -> Dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


# 1. OpenAI Juror (gpt-4o)
async def call_openai_juror(job_details: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY missing.")
        return {"model": "gpt-4o", "worker_bps": 5000, "reasoning": "Fallback: Key missing."}
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        prompt = (
            f"You are a neutral decentralized court juror in AgentCourt.\n"
            f"Evaluate this task deliverable submission:\n"
            f"Job ID: {job_details.get('job_id')}\n"
            f"Deliverable Hash: {job_details.get('deliverable_hash')}\n\n"
            f"Respond ONLY with a JSON object:\n"
            f'{{"worker_bps": <integer between 0 and 10000>, "reasoning": "<concise justification>"}}'
        )
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
async def call_anthropic_juror(job_details: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing.")
        return {"model": "claude", "worker_bps": 5000, "reasoning": "Fallback: Key missing."}
    
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=api_key)
        prompt = (
            f"You are a neutral decentralized court juror in AgentCourt.\n"
            f"Evaluate this task deliverable submission:\n"
            f"Job ID: {job_details.get('job_id')}\n"
            f"Deliverable Hash: {job_details.get('deliverable_hash')}\n\n"
            f"Respond ONLY with a raw JSON object:\n"
            f'{{"worker_bps": <integer between 0 and 10000>, "reasoning": "<concise justification>"}}'
        )
        
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
async def call_gemini_juror(job_details: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY missing.")
        return {"model": "gemini", "worker_bps": 5000, "reasoning": "Fallback: Key missing."}
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are a neutral decentralized court juror in AgentCourt.\n"
            f"Evaluate this task deliverable submission:\n"
            f"Job ID: {job_details.get('job_id')}\n"
            f"Deliverable Hash: {job_details.get('deliverable_hash')}\n\n"
            f"Respond ONLY with a raw JSON object:\n"
            f'{{"worker_bps": <integer between 0 and 10000>, "reasoning": "<concise justification>"}}'
        )
        
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
    job_details = {"job_id": job_id, "deliverable_hash": deliverable_hash}
    logger.info(f"Dispatching Job #{job_id} to 3-juror quorum...")

    results: List[Dict[str, Any]] = await asyncio.gather(
        call_openai_juror(job_details),
        call_anthropic_juror(job_details),
        call_gemini_juror(job_details)
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

