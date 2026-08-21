import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from google import genai
from google.genai import types
from vector_precedents import find_relevant_precedents, format_precedents_for_prompt, record_new_precedent

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT_TEMPLATE = """You are an impartial AI juror in a decentralized escrow dispute protocol (AgentCourt).

{precedents_context}

Current Case Task Specification:
{spec}

Current Case Delivered Work:
{deliv}

Evaluate if the deliverable satisfies the task requirements consistently with prior rulings.
Respond strictly in valid JSON format:
{{
  "basis_points": <integer from 0 to 10000>,
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<concise 1-2 sentence justification, citing any relevant precedent if applicable>"
}}"""

async def query_gpt4o(task_spec: str, deliverable: str, precedents_context: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(precedents_context=precedents_context, spec=task_spec, deliv=deliverable)
    res = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    data = json.loads(res.choices[0].message.content)
    data["juror"] = "GPT-4o"
    return data

async def query_juror_2(task_spec: str, deliverable: str, precedents_context: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(precedents_context=precedents_context, spec=task_spec, deliv=deliverable)
    # 1. Try Anthropic
    for model_name in ["claude-3-5-sonnet-latest", "claude-3-haiku-20240307", "claude-3-sonnet-20240229"]:
        try:
            res = await anthropic_client.messages.create(
                model=model_name,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            text = res.content[0].text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            data = json.loads(text)
            data["juror"] = "Claude"
            return data
        except Exception:
            continue
            
    # 2. Fallback to GPT-4o-mini
    res = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    data = json.loads(res.choices[0].message.content)
    data["juror"] = "GPT-4o-Mini (Alt-Juror)"
    return data

async def query_juror_3(task_spec: str, deliverable: str, precedents_context: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(precedents_context=precedents_context, spec=task_spec, deliv=deliverable)
    # 1. Try Gemini models
    for gemini_model in ["gemini-2.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]:
        try:
            res = gemini_client.models.generate_content(
                model=gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(res.text)
            data["juror"] = f"Gemini ({gemini_model})"
            return data
        except Exception:
            continue
            
    # 2. Fallback to GPT-4o-mini
    res = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    data = json.loads(res.choices[0].message.content)
    data["juror"] = "OpenAI-Mini (Alt-Juror)"
    return data

async def deliberate_job(job_id: int, deliverable_hash: str, task_spec: str = None, deliverable_text: str = None) -> dict:
    spec = task_spec or f"Job #{job_id} task agreement on Base Sepolia."
    deliv = deliverable_text or f"Deliverable Hash submitted on-chain: {deliverable_hash}"
    
    # 1. Retrieve Stare Decisis Precedents from ChromaDB
    precedents = find_relevant_precedents(spec, deliv, top_k=2)
    precedents_context = format_precedents_for_prompt(precedents)
    
    # 2. Parallel AI Jury Deliberation
    results = await asyncio.gather(
        query_gpt4o(spec, deliv, precedents_context),
        query_juror_2(spec, deliv, precedents_context),
        query_juror_3(spec, deliv, precedents_context),
        return_exceptions=True
    )
    
    valid_jurors = [r for r in results if isinstance(r, dict)]
    bps_list = [r["basis_points"] for r in valid_jurors]
    consensus_bps = int(sorted(bps_list)[len(bps_list) // 2]) if bps_list else 0
    opinions = " | ".join([f"{j['juror']}: {j['basis_points']} bps ({j['reasoning']})" for j in valid_jurors])
    
    # 3. Record newly settled case as legal precedent for future stare decisis
    try:
        record_new_precedent(
            case_id=str(job_id),
            title=f"Escrow Case #{job_id}",
            task_spec=spec,
            fact_summary=f"Deliverable: {deliv[:150]}... | Consensus: {consensus_bps} bps | Opinions: {opinions[:200]}",
            ruling_basis_points=consensus_bps
        )
    except Exception as e:
        print(f"[Warning] Failed to record precedent for Case #{job_id}: {e}")
    
    return {
        "consensus_bps": consensus_bps,
        "opinion": opinions,
        "juror_breakdown": valid_jurors,
        "outliers_dropped": []
    }
