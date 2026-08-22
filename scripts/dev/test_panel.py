import os
import warnings
from dotenv import load_dotenv
import anthropic
from openai import OpenAI
from google import genai

warnings.filterwarnings("ignore")
load_dotenv()

print("\n==========================================")
print("     AGENT COURT AI JUROR PANEL TEST      ")
print("==========================================\n")

# 1. Claude Juror (Anthropic - Auto Discovery)
claude_key = os.getenv("ANTHROPIC_API_KEY")
if not claude_key:
    print("[-] Claude  : ANTHROPIC_API_KEY missing in .env")
else:
    try:
        client = anthropic.Anthropic(api_key=claude_key)
        # Fetch active models on your account
        models_page = client.models.list()
        active_model = models_page.data[0].id
        
        c_res = client.messages.create(
            model=active_model,
            max_tokens=50,
            messages=[{"role": "user", "content": f"Respond strictly with: Juror 1 ({active_model}) Online & Ready."}]
        )
        print(f"[+] Claude  : {c_res.content[0].text.strip()}")
    except Exception as e:
        print(f"[-] Claude  : Error -> {e}")

# 2. GPT Juror (OpenAI)
try:
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    o_res = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Respond strictly with: Juror 2 (GPT-4o Mini) Online & Ready."}],
        max_tokens=50
    )
    print("[+] OpenAI  : " + o_res.choices[0].message.content.strip())
except Exception as e:
    print("[-] OpenAI  : Error ->", e)

# 3. Gemini Juror (Google)
try:
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    chat = gemini_client.chats.create(model="gemini-3.6-flash")
    g_res = chat.send_message("Respond strictly with: Juror 3 (Gemini Flash) Online & Ready.")
    print("[+] Gemini  : " + g_res.text.strip())
except Exception as e:
    print("[-] Gemini  : Error ->", e)

print("\n==========================================\n")
