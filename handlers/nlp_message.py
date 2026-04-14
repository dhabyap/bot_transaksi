import database
from ai_brain import get_json_data_from_text
import time

# Dictionary untuk menyimpan timestamp pemrosesan AI terakhir per user (Rate Limiting)
last_ai_calls = {}
RATE_LIMIT_COOLDOWN = 10  # detik

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
        
        # --- RATE LIMITING CHECK ---
        now = time.time()
        if user_id in last_ai_calls:
            elapsed = now - last_ai_calls[user_id]
            if elapsed < RATE_LIMIT_COOLDOWN:
                remaining = int(RATE_LIMIT_COOLDOWN - elapsed)
                bot.reply_to(message, f"⚠️ *Terlalu cepat!* Mohon tunggu {remaining} detik lagi sebelum mencatat transaksi baru... 🙏", parse_mode='Markdown')
                return
        
        # Update timestamp pemrosesan terakhir
        last_ai_calls[user_id] = now
        
        # Process text with AI
        results = get_json_data_from_text(text)
        
        # Jika hasil bukan list (misal {"error": true}), handle error
        if isinstance(results, dict) and results.get("error"):
            bot.reply_to(message, "❌ Maaf, saya tidak menangkap adanya transaksi keuangan. Pastikan formatnya jelas (contoh: 'beli makan 20rb' atau 'gajian 4 juta').")
            return
            
        success_count = 0
        summary_lines = []
        
        try:
            for data in results:
                tipe = data.get("tipe", "").lower()
                item = data.get("item", "")
                nominal = float(data.get("nominal", 0))
                kategori = data.get("kategori", "")
                
                # Save to database based on type
                try:
                    if tipe == "saldo":
                        # Reconcile balance
                        current_balance = database.get_user_balance(user_id)
                        diff = nominal - current_balance
                        
                        if diff == 0:
                            summary_lines.append(f"💰 *Saldo:* Sudah sesuai di angka Rp {nominal:,.0f}")
                            success_count += 1
                            continue

                        # Determine if reconciliation is income or expense
                        rec_tipe = "pemasukan" if diff > 0 else "pengeluaran"
                        rec_nominal = abs(diff)
                        rec_item = "Penyesuaian Saldo"
                        
                        last_id = database.insert_transaction(user_id, rec_tipe, rec_item, rec_nominal, "lainnya")
                        
                        icon = "💰"
                        summary_lines.append(
                            f"{icon} *Saldo disesuaikan:* Rp {current_balance:,.0f} ➔ Rp {nominal:,.0f} (`T-{last_id}`)"
                        )
                        success_count += 1

                    elif tipe in ["pemasukan", "pengeluaran", "investasi"]:
                        last_id = database.insert_transaction(user_id, tipe, item, nominal, kategori)
                        
                        if tipe == "pemasukan":
                            icon = "🟢"
                        elif tipe == "investasi":
                            icon = "🔵"
                        else:
                            icon = "🔴"
                        
                        summary_lines.append(
                            f"{icon} *{tipe.capitalize()}:* {item} — Rp {nominal:,.0f} (`T-{last_id}`)"
                        )
                        success_count += 1
                except Exception as e:
                    print(f"Error inserting transaction: {e}")

            if success_count > 0:
                reply = "✅ *Berhasil mencatat " + (f"{success_count} transaksi" if success_count > 1 else "transaksi") + ":*\n\n"
                reply += "\n".join(summary_lines)
                bot.reply_to(message, reply, parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ Gagal mencatat transaksi. Pastikan format pesan sudah benar.")

        except Exception as e:
            print(f"Error in handle_text: {e}")
            bot.reply_to(message, "❌ Terjadi kesalahan sistem saat memproses permintaan Anda. Silakan coba lagi nanti.")