import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import database
from ai_brain import get_json_data_from_text
import calendar
from datetime import datetime

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
    database.upsert_user(message.from_user)
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

MONTH_NAMES = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def generate_report_text(report, month, year):
    pemasukan = report.get('pemasukan', 0) or 0
    pengeluaran = report.get('pengeluaran', 0) or 0
    saldo = pemasukan - pengeluaran
    
    month_name = MONTH_NAMES.get(month, "")
    last_day = calendar.monthrange(year, month)[1]
    
    report_text = (
        f"📊 *Laporan Keuangan*\n"
        f"🗓 *Periode:* 1 {month_name} {year} - {last_day} {month_name} {year}\n\n"
        f"🟢 Pemasukan: Rp {pemasukan:,.0f}\n"
        f"🔴 Pengeluaran: Rp {pengeluaran:,.0f}\n"
        "-------------------------\n"
        f"⚖️ Saldo: Rp {saldo:,.0f}"
    )
    return report_text

def get_report_markup(month, year):
    markup = InlineKeyboardMarkup()
    
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
        
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1
        
    btn_prev = InlineKeyboardButton("⬅️ Bulan Sebelumnya", callback_data=f"report_{prev_month}_{prev_year}")
    btn_next = InlineKeyboardButton("Bulan Berikutnya ➡️", callback_data=f"report_{next_month}_{next_year}")
    
    markup.row(btn_prev, btn_next)
    return markup

@bot.message_handler(commands=['laporan'])
def send_report(message):
    database.upsert_user(message.from_user)
    user_id = message.from_user.id
    
    now = datetime.now()
    month = now.month
    year = now.year
    month_str = f"{year}-{month:02d}"
    
    report = database.get_monthly_report(user_id, month_str)
    
    report_text = generate_report_text(report, month, year)
    markup = get_report_markup(month, year)
    
    bot.reply_to(message, report_text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('report_'))
def callback_report(call):
    user_id = call.from_user.id
    _, month_str, year_str = call.data.split('_')
    month = int(month_str)
    year = int(year_str)
    target_month_str = f"{year}-{month:02d}"
    
    report = database.get_monthly_report(user_id, target_month_str)
    
    report_text = generate_report_text(report, month, year)
    markup = get_report_markup(month, year)
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text=report_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['riwayat'])
def send_history(message):
    database.upsert_user(message.from_user)
    user_id = message.from_user.id
    history = database.get_history(user_id)
    
    if not history:
        bot.reply_to(message, "📭 Belum ada riwayat aktivitas.")
        return
        
    text = "📜 *Riwayat Aktivitas Terbaru:*\n\n"
    for item in history:
        prefix = item['prefix']
        item_id = item['id']
        label = item['label'].capitalize()
        name = item['item']
        val = item['val']
        
        if prefix == 'T':
            text += f"🔹 `[{prefix}-{item_id}]` *{label}*: {name} (Rp {val:,.0f})\n"
        else:
            text += f"🔸 `[{prefix}-{item_id}]` *Stok {label}*: {name} ({int(val)} unit)\n"
            
    text += "\n💡 Gunakan `/hapus <ID>` atau `/edit <ID> <Kalimat Baru>`"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['hapus'])
def delete_item(message):
    database.upsert_user(message.from_user)
    user_id = message.from_user.id
    parts = message.text.split()
    
    if len(parts) < 2:
        bot.reply_to(message, "❌ Format salah. Gunakan: `/hapus <ID>`\nContoh: `/hapus T-10`", parse_mode='Markdown')
        return
        
    raw_id = parts[1].upper()
    try:
        prefix, item_id = raw_id.split('-')
        item_id = int(item_id)
        
        success = False
        if prefix == 'T':
            success = database.delete_transaction(item_id, user_id)
        elif prefix == 'I':
            success = database.delete_inventory(item_id, user_id)
            
        if success:
            bot.reply_to(message, f"✅ Data `{raw_id}` berhasil dihapus.")
        else:
            bot.reply_to(message, f"❌ Data `{raw_id}` tidak ditemukan atau bukan milik Anda.")
    except Exception:
        bot.reply_to(message, "❌ ID tidak valid. Contoh ID: `T-10` atau `I-5`", parse_mode='Markdown')

@bot.message_handler(commands=['edit'])
def edit_item(message):
    database.upsert_user(message.from_user)
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=2)
    
    if len(parts) < 3:
        bot.reply_to(message, "❌ Format salah. Gunakan: `/edit <ID> <Kalimat Baru>`\nContoh: `/edit T-10 gaji naik 5 juta`", parse_mode='Markdown')
        return
        
    raw_id = parts[1].upper()
    new_text = parts[2]
    
    bot.send_chat_action(message.chat.id, 'typing')
    data = get_json_data_from_text(new_text)
    
    if data.get("error"):
        bot.reply_to(message, "❌ Gagal memproses kalimat baru. Pastikan formatnya jelas.")
        return
        
    try:
        prefix, item_id = raw_id.split('-')
        item_id = int(item_id)
        
        tipe = data.get("tipe", "").lower()
        item_name = data.get("item", "")
        nominal = float(data.get("nominal", 0))
        kategori = data.get("kategori", "")
        
        success = False
        if prefix == 'T' and tipe in ["pemasukan", "pengeluaran"]:
            success = database.update_transaction(item_id, user_id, tipe, item_name, nominal, kategori)
        elif prefix == 'I' and tipe == "stok":
            status = "tambah" if nominal > 0 else "kurang"
            success = database.update_inventory(item_id, user_id, item_name, int(abs(nominal)), status)
        else:
            bot.reply_to(message, "❌ Tipe data tidak cocok dengan ID yang diberikan.")
            return
            
        if success:
            bot.reply_to(message, f"✅ Data `{raw_id}` berhasil diperbarui.")
        else:
            bot.reply_to(message, f"❌ Data `{raw_id}` tidak ditemukan atau bukan milik Anda.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi kesalahan: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    database.upsert_user(message.from_user)
    user_id = message.from_user.id
    text = message.text
    
    # Log incoming message
    database.insert_chat_log(user_id, text)
    
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
            # Ambil ID terakhir untuk ditampilkan (optional tapi membantu)
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT LAST_INSERT_ID()")
            last_id = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            reply = f"✅ Berhasil mencatat *{tipe.capitalize()}*: {item} (Rp {nominal:,.0f})\nID: `T-{last_id}`"
        elif tipe == "stok":
            status = "tambah" if nominal > 0 else "kurang"
            database.insert_inventory(user_id, item, int(abs(nominal)), status)
            # Ambil ID terakhir
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT LAST_INSERT_ID()")
            last_id = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            reply = f"✅ Berhasil mencatat *Stok {status}*: {item} ({int(abs(nominal))} unit)\nID: `I-{last_id}`"
        else:
            bot.reply_to(message, "❌ Tipe data tidak dikenali dari hasil AI.")
            return
            
        bot.reply_to(message, reply, parse_mode='Markdown')
        
    except Exception as e:
        default_error_msg = f"❌ Terjadi kesalahan saat menyimpan data ke database:\n{str(e)}"
        bot.reply_to(message, default_error_msg)

if __name__ == "__main__":
    # Setup auto-suggest / menu perintah di Telegram
    bot.set_my_commands([
        telebot.types.BotCommand("/start", "Menjalankan ulang bot"),
        telebot.types.BotCommand("/help", "Info cara penggunaan bot"),
        telebot.types.BotCommand("/laporan", "Melihat ringkasan keuangan"),
        telebot.types.BotCommand("/riwayat", "Melihat riwayat transaksi & stok")
    ])
    print("Bot is running...")
    bot.infinity_polling()
