import os
import json
import requests
from google import genai
from google.genai import types 
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# System instruction yang padat agar model AI lebih cepat merespons
SYSTEM_INSTRUCTION = """
Kamu adalah asisten AI spesialis pencatatan keuangan pribadi. Tugasmu adalah mengekstrak data dari pesan pengguna ke format JSON murni.

SKEMA JSON:
{
  "tipe": "pemasukan" | "pengeluaran" | "investasi",
  "item": "deskripsi singkat transaksi",
  "nominal": angka integer,
  "kategori": "makanan_minuman" | "transportasi" | "tagihan_rutin" | "hiburan" | "belanja_pribadi" | "pendapatan_gaji" | "pendapatan_sampingan" | "aset_investasi" | "lainnya"
}

ATURAN KETAT:
1. Konversi singkatan angka: "k" / "rb" = 1000, "jt" / "juta" = 1000000.
2. Jika nominal dalam teks (misal: "setengah juta", "seratus ribu"), ubah ke angka integer (misal: 500000, 100000).
3. Fokus pada uang masuk, keluar, atau investasi.
4. Jawaban HANYA berupa JSON murni tanpa teks pengantar. Jika error, kembalikan {"error": true}.
"""

def call_gemini(text: str) -> str:
    """Memanggil Google Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan")
    
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    return response.text.strip()

def call_openai_compatible(text: str, api_key: str, base_url: str, model: str) -> str:
    """Wrapper dinamis untuk berbagai provider berbasis OpenAI standard."""
    if not api_key:
        raise ValueError(f"API key untuk {base_url} (model {model}) tidak ditemukan")
    
    client = OpenAI(base_url=base_url, api_key=api_key)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": text}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content.strip()

def call_cohere(text: str) -> str:
    """Memanggil Cohere API secara native (tanpa openai wrapper)"""
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        raise ValueError("COHERE_API_KEY tidak ditemukan")
    
    response = requests.post(
        "https://api.cohere.com/v1/chat",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "command-r",
            "message": text,
            "preamble": SYSTEM_INSTRUCTION,
            "temperature": 0.1
        }
    )
    response.raise_for_status()
    return response.json().get("text", "").strip()

def call_provider(provider: str, text: str) -> str:
    """Routing request menuju engine provider yang tepat berdasarkan key."""
    if provider == "gemini":
        return call_gemini(text)
    elif provider == "groq":
        return call_openai_compatible(text, os.getenv("GROQ_API_KEY"), "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile")
    elif provider == "openrouter":
        return call_openai_compatible(text, os.getenv("OPENROUTER_API_KEY"), "https://openrouter.ai/api/v1", "meta-llama/llama-3-8b-instruct:free")
    elif provider == "deepseek":
        return call_openai_compatible(text, os.getenv("DEEPSEEK_API_KEY"), "https://api.deepseek.com", "deepseek-chat")
    elif provider == "together":
        return call_openai_compatible(text, os.getenv("TOGETHER_API_KEY"), "https://api.together.xyz/v1", "meta-llama/Llama-2-13b-chat-hf")
    elif provider == "huggingface":
        return call_openai_compatible(text, os.getenv("HF_API_KEY"), "https://api-inference.huggingface.co/v1/chat/completions", "mistralai/Mistral-7B-Instruct-v0.2")
    elif provider == "cohere":
        return call_cohere(text)
    else:
        raise ValueError(f"Provider {provider} tidak didukung")

def extract_json_from_text(text: str) -> str:
    """Ekstraksi JSON dari teks, menangani kemungkinan filler atau markdown."""
    text = text.strip()
    
    # 1. Coba cari blok markdown ```json ... ```
    if "```json" in text:
        try:
            return text.split("```json")[1].split("```")[0].strip()
        except: pass
    
    # 2. Coba cari blok markdown ``` ... ```
    if "```" in text:
        try:
            return text.split("```")[1].split("```")[0].strip()
        except: pass

    # 3. Cari dari kurung kurawal pertama sampai terakhir (paling robust)
    start_index = text.find('{')
    end_index = text.rfind('}')
    if start_index != -1 and end_index != -1 and end_index > start_index:
        return text[start_index:end_index+1].strip()
    
    return text

def get_json_data_from_text(text: str) -> dict:
    """
    Dispatcher utama yang menggunakan mekanisme fallback antar berbagai LLM provider tanpa batas.
    """
    fallback_order = os.getenv("LLM_FALLBACK_ORDER", "gemini,groq,openrouter,deepseek,cohere,together,huggingface").split(",")
    
    # Map provider ke nama environment variabel key-nya untuk pre-validation
    key_map = {
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "cohere": "COHERE_API_KEY",
        "together": "TOGETHER_API_KEY",
        "huggingface": "HF_API_KEY"
    }

    for provider in fallback_order:
        provider = provider.strip().lower()
        if not provider: continue
        
        # Pre-validation: Skip jika API key tidak ada
        env_key = key_map.get(provider)
        if env_key and not os.getenv(env_key):
            print(f"[ai_brain] Skip {provider}: {env_key} tidak disetel.")
            continue

        try:
            print(f"[ai_brain] Mencoba menggunakan provider: {provider}...")
            response_text = call_provider(provider, text)
            
            # Bersihkan dan ambil JSON murni
            json_text = extract_json_from_text(response_text)
                
            data = json.loads(json_text)
            
            # Validasi minimal struktur data
            if not any(k in data for k in ["tipe", "nominal", "item"]):
                raise ValueError("JSON berhasil diparsing tapi struktur tidak sesuai")

            print(f"[ai_brain] Memanfaatkan tenaga {provider.capitalize()} berhasil!")
            return data
            
        except Exception as e:
            # Jika KeyError / Network Error / Rate Limit / Parsing Error dll
            error_msg = str(e)
            if "429" in error_msg or "rate_limit" in error_msg.lower():
                print(f"[ai_brain] Provider {provider} mencapai rate limit.")
            else:
                print(f"[ai_brain] Router gagal di jalur {provider}. (Error: {error_msg})")
            
            print(f"[ai_brain] Melompat ke backup selanjutnya...")
            continue 
            
    print("[ai_brain] FATAL: Semua LLM provider backup gagal atau API Key tidak disetel.")
    return {"error": True}