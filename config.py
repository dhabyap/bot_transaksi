import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN       = os.getenv("TELEGRAM_BOT_TOKEN")
ERROR_BOT_TOKEN = os.getenv("ERROR_BOT_TOKEN", BOT_TOKEN) # Pakai token utama jika token error kosong
ADMIN_CHAT_ID   = os.getenv("ADMIN_CHAT_ID", "") 

if not BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN is not set in .env")
    exit(1)

if not ADMIN_CHAT_ID:
    print("Warning: ADMIN_CHAT_ID belum diset — notifikasi error tidak akan dikirim.")

MONTH_NAMES = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}
TRANSACTION_CATEGORIES = [
    "makanan_minuman", "transportasi", "tagihan_rutin", "hiburan", 
    "belanja_pribadi", "pendapatan_gaji", "pendapatan_sampingan", 
    "aset_investasi", "lainnya"
]
