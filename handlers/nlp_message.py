import database
from ai_brain import get_json_data_from_text

def register_handlers(bot):
    # Gunakan lambda yang menangkap semua teks, tapi pastikan bukan command
    @bot.message_handler(func=lambda message: True)
    def handle_text(message):
        # Abaikan pesan yang diawali dengan '/' agar command yang typo tidak diproses AI
        if message.text.startswith('/'):
            bot.reply_to(message, "❌ Command tidak dikenali. Ketik pesan biasa untuk mencatat keuangan.")
            return
            
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
            bot.reply_to(message, "❌ Maaf, saya tidak menangkap adanya transaksi keuangan. Pastikan formatnya jelas (contoh: 'beli makan 20rb' atau 'gajian 4 juta').")
            return
            
        tipe = data.get("tipe", "").lower()
        item = data.get("item", "")
        nominal = float(data.get("nominal", 0))
        kategori = data.get("kategori", "")
        
        # Save to database based on type
        try:
            # Sekarang hanya fokus pada pemasukan, pengeluaran, dan investasi
            if tipe in ["pemasukan", "pengeluaran", "investasi"]:
                last_id = database.insert_transaction(user_id, tipe, item, nominal, kategori)
                
                if tipe == "pemasukan":
                    icon = "🟢"
                elif tipe == "investasi":
                    icon = "🔵"
                else:
                    icon = "🔴"
                    
                reply = (
                    f"{icon} *Berhasil dicatat!*\n\n"
                    f"🔹 *Tipe:* {tipe.capitalize()}\n"
                    f"🔹 *Item:* {item}\n"
                    f"🔹 *Nominal:* Rp {nominal:,.0f}\n"
                    f"🔹 *Kategori:* {kategori.replace('_', ' ').capitalize()}\n\n"
                    f"🆔 *ID:* `T-{last_id}`"
                )
                bot.reply_to(message, reply, parse_mode='Markdown')
                
            else:
                bot.reply_to(message, "❌ Tipe data tidak dikenali dari hasil AI. Pastikan AI mengembalikan format yang benar.")
                
        except Exception as e:
            print(f"Error in handle_text: {e}")
            bot.reply_to(message, "❌ Terjadi kesalahan sistem saat memproses permintaan Anda. Silakan coba lagi nanti.")