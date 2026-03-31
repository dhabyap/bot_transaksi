import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
# Use Gemini 1.5 Flash
model = genai.GenerativeModel('gemini-1.5-flash')

def get_json_data_from_text(text: str) -> dict:
    """
    Sends the user text to Gemini API and returns a parsed JSON dictionary.
    """
    system_instruction = """
Kamu adalah asisten keuangan dan stok barang. Ekstrak data dari pesan user menjadi JSON murni.
Aturan:
'gaji 4 juta' -> {"tipe": "pemasukan", "item": "gaji", "nominal": 4000000, "kategori": "pendapatan"}
'beli sabun 20rb' -> {"tipe": "pengeluaran", "item": "sabun", "nominal": 20000, "kategori": "operasional"}
'stok handuk 5 unit' -> {"tipe": "stok", "item": "handuk", "nominal": 5, "kategori": "inventaris"}
Hanya balas dalam format JSON murni. Jika tidak mengerti, balas {"error": true}.
    """
    
    prompt = f"{system_instruction}\n\nUser input: {text}"
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        data = json.loads(response_text)
        return data
    except Exception as e:
        print(f"Error calling Gemini AI: {e}")
        return {"error": True}
