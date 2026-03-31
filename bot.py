import os
import telebot
from dotenv import load_dotenv
import database
from ai_brain import get_json_data_from_text

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN is not set in .env")
    exit(1)

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize database
database.init_db()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 *Personal Finance & Inventory Bot*\n\n"
        "Halo! Saya adalah asisten pintar untuk manajemen keuangan dan stok barang.\n\n"
        "Cukup kirim pesan seperti:\n"
        "• _'gaji 4 juta'_\n"
        "• _'beli sabun 20rb'_\n"
        "• _'stok handuk 5 unit'_\n\n"
        "Gunakan perintah /laporan untuk melihat ringkasan keuangan bulan ini."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['laporan'])
def send_report(message):
    user_id = message.from_user.id
    report = database.get_monthly_report(user_id)
    pemasukan = report["pemasukan"] or 0
    pengeluaran = report["pengeluaran"] or 0
    saldo = pemasukan - pengeluaran
    
    report_text = (
        "📊 *Laporan Bulan Ini*\n\n"
        f"🟢 Pemasukan: Rp {pemasukan:,.0f}\n"
        f"🔴 Pengeluaran: Rp {pengeluaran:,.0f}\n"
        "-------------------------\n"
        f"💰 *Saldo: Rp {saldo:,.0f}*"
    )
    bot.reply_to(message, report_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text
    
    # Show typing status while processing
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Process text with AI
    data = get_json_data_from_text(text)
    
    if data.get("error"):
        bot.reply_to(message, "❌ Maaf, saya tidak mengerti pesan Anda. Coba gunakan format yang lebih jelas.")
        return
        
    tipe = data.get("tipe", "").lower()
    item = data.get("item", "")
    nominal = float(data.get("nominal", 0))
    kategori = data.get("kategori", "")
    
    # Save to database based on type
    try:
        if tipe in ["pemasukan", "pengeluaran"]:
            database.insert_transaction(user_id, tipe, item, nominal, kategori)
            reply = f"✅ Berhasil mencatat *{tipe.capitalize()}*: {item} senilai Rp {nominal:,.0f}"
        elif tipe == "stok":
            status = "tambah" if nominal > 0 else "kurang"
            database.insert_inventory(user_id, item, int(abs(nominal)), status)
            reply = f"✅ Berhasil mencatat *Stok {status}*: {item} ({int(nominal)} unit)"
        else:
            bot.reply_to(message, "❌ Tipe data tidak dikenali dari hasil AI.")
            return
            
        bot.reply_to(message, reply, parse_mode='Markdown')
        
    except Exception as e:
        default_error_msg = f"❌ Terjadi kesalahan saat menyimpan data ke database:\n{str(e)}"
        bot.reply_to(message, default_error_msg)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
