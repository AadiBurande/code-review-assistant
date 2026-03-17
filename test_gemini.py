# test_gemini.py
from dotenv import load_dotenv
import os
load_dotenv()

from langchain_core.messages import HumanMessage

provider = os.getenv("LLM_PROVIDER", "ollama").lower()
print(f"Testing provider: {provider}\n")

# ── Ollama Test ───────────────────────────────────────────────────────────────
if provider == "ollama":
    from langchain_ollama import ChatOllama

    models = [
        os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M"),
        "codellama:7b-instruct-q4_K_M",
        "mistral:7b-instruct-q4_K_M",
    ]

    for model in models:
        print(f"Testing {model}...")
        try:
            llm = ChatOllama(model=model, temperature=0.1, num_predict=100)
            response = llm.invoke([HumanMessage(content='Return only this JSON array: [{"status": "ok"}]')])
            print(f"  SUCCESS: {response.content.strip()[:120]}")
            print(f"\n>>> Working model: {model}")
            break
        except Exception as e:
            print(f"  FAILED: {str(e)[:150]}")

# ── Gemini Test ───────────────────────────────────────────────────────────────
elif provider == "gemini":
    from langchain_google_genai import ChatGoogleGenerativeAI

    key = os.getenv("GEMINI_API_KEY")
    print(f"API Key loaded: {key[:12]}...")

    models = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
    ]

    for model in models:
        print(f"\nTesting {model}...")
        try:
            llm = ChatGoogleGenerativeAI(model=model, google_api_key=key, max_output_tokens=50)
            response = llm.invoke([HumanMessage(content="Say hello in one word")])
            print(f"  SUCCESS: {response.content.strip()}")
            print(f"\n>>> Working model: {model}")
            break
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {str(e)[:200]}")

# ── Groq Test ─────────────────────────────────────────────────────────────────
elif provider == "groq":
    from langchain_groq import ChatGroq

    key = os.getenv("GROQ_API_KEY")
    print(f"API Key loaded: {key[:8]}...")

    try:
        llm = ChatGroq(model=os.getenv("MODEL_NAME", "llama-3.1-8b-instant"), api_key=key, max_tokens=50)
        response = llm.invoke([HumanMessage(content="Say hello in one word")])
        print(f"  SUCCESS: {response.content.strip()}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {str(e)[:200]}")

# ── OpenAI Test ───────────────────────────────────────────────────────────────
elif provider == "openai":
    from langchain_openai import ChatOpenAI

    key = os.getenv("OPENAI_API_KEY")
    print(f"API Key loaded: {key[:8]}...")

    try:
        llm = ChatOpenAI(model=os.getenv("MODEL_NAME", "gpt-4o"), api_key=key, max_tokens=50)
        response = llm.invoke([HumanMessage(content="Say hello in one word")])
        print(f"  SUCCESS: {response.content.strip()}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {str(e)[:200]}")
