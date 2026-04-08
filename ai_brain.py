import os
import json
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
2. Fokus pada uang masuk, keluar, atau investasi.
3. Jika input tidak valid atau bukan transaksi, balas HANYA dengan: {"error": true}.
"""

def call_gemini(text: str) -> str:
    """Memanggil Google Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan")
    
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.0-flash', # Updated to latest flash model
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    return response.text.strip()

def call_groq(text: str) -> str:
    """Memanggil Groq API (OpenAI Compatible)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan")
    
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", # High quality model available on Groq
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    return response.choices[0].message.content.strip()

def get_json_data_from_text(text: str) -> dict:
    """
    Dispatcher utama yang menggunakan mekanisme fallback antar LLM provider.
    """
    fallback_order = os.getenv("LLM_FALLBACK_ORDER", "gemini,groq").split(",")
    
    for provider in fallback_order:
        provider = provider.strip().lower()
        try:
            print(f"[ai_brain] Mencoba menggunakan provider: {provider}...")
            
            if provider == "gemini":
                response_text = call_gemini(text)
            elif provider == "groq":
                response_text = call_groq(text)
            else:
                continue # Provider tidak dikenal
                
            # Bersihkan output markdown jika ada
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
                
            data = json.loads(response_text)
            print(f"[ai_brain] Berhasil menggunakan {provider}.")
            return data
            
        except Exception as e:
            print(f"[ai_brain] Gagal menggunakan {provider}: {e}")
            continue # Lanjut ke provider berikutnya
            
    print("[ai_brain] Semua LLM provider gagal.")
    return {"error": True}