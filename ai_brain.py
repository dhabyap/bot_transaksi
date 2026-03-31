import os
import json
from google import genai
from google.genai import types 
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

def get_json_data_from_text(text: str) -> dict:
    """
    Mengirim teks pengguna ke Gemini API dan mengembalikan dictionary JSON untuk jurnal keuangan pribadi.
    """
    if not client:
        return {"error": True, "message": "API Key tidak ditemukan"}

    # System instruction yang padat agar model Flash lebih cepat merespons
    system_instruction = """
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
    
    try:
        # Menggunakan model Flash (gratis & cepat)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=text, # Menggunakan parameter 'text' dari fungsi, bukan 'prompt'
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json", # Paksa AI agar fokus menghasilkan JSON
                temperature=0.1
            )
        )
        
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        data = json.loads(response_text)
        return data
        
    except Exception as e:
        print(f"Error calling Gemini AI: {e}")
        return {"error": True}