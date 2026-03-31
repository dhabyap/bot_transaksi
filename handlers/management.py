import database
from ai_brain import get_json_data_from_text

def register_handlers(bot):
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
            
            # Hanya memproses ID Transaksi (T)
            if prefix == 'T':
                success = database.delete_transaction(item_id, user_id)
                if success:
                    bot.reply_to(message, f"✅ Data `{raw_id}` berhasil dihapus.", parse_mode='Markdown')
                else:
                    bot.reply_to(message, f"❌ Data `{raw_id}` tidak ditemukan atau bukan milik Anda.")
            else:
                bot.reply_to(message, "❌ ID tidak valid. Pastikan menggunakan awalan T (contoh: `T-10`).", parse_mode='Markdown')
                
        except ValueError:
            # Menangkap error jika split('-') gagal atau item_id bukan angka
            bot.reply_to(message, "❌ Format ID salah. Contoh yang benar: `T-10`", parse_mode='Markdown')

    @bot.message_handler(commands=['edit'])
    def edit_item(message):
        database.upsert_user(message.from_user)
        user_id = message.from_user.id
        # Gunakan maxsplit=2 agar kalimat baru tidak terpotong-potong
        parts = message.text.split(maxsplit=2) 
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ Format salah. Gunakan: `/edit <ID> <Kalimat Baru>`\nContoh: `/edit T-10 gaji naik 5 juta`", parse_mode='Markdown')
            return
            
        raw_id = parts[1].upper()
        new_text = parts[2]
        
        bot.send_chat_action(message.chat.id, 'typing')
        data = get_json_data_from_text(new_text)
        
        if data.get("error"):
            bot.reply_to(message, "❌ Gagal memproses kalimat baru. Pastikan formatnya jelas dan terkait keuangan.")
            return
            
        try:
            prefix, item_id = raw_id.split('-')
            item_id = int(item_id)
            
            tipe = data.get("tipe", "").lower()
            item_name = data.get("item", "")
            nominal = float(data.get("nominal", 0))
            kategori = data.get("kategori", "")
            
            # Tambahkan "investasi" ke dalam list tipe yang diizinkan
            if prefix == 'T' and tipe in ["pemasukan", "pengeluaran", "investasi"]:
                success = database.update_transaction(item_id, user_id, tipe, item_name, nominal, kategori)
                
                if success:
                    # Berikan feedback yang informatif agar kamu tahu hasil editannya
                    feedback = (
                        f"✅ Data `{raw_id}` berhasil diperbarui:\n\n"
                        f"🔹 *Tipe:* {tipe.capitalize()}\n"
                        f"🔹 *Item:* {item_name}\n"
                        f"🔹 *Nominal:* Rp {nominal:,.0f}\n"
                        f"🔹 *Kategori:* {kategori.replace('_', ' ').capitalize()}"
                    )
                    bot.reply_to(message, feedback, parse_mode='Markdown')
                else:
                    bot.reply_to(message, f"❌ Data `{raw_id}` tidak ditemukan atau bukan milik Anda.")
            else:
                bot.reply_to(message, "❌ Gagal memperbarui. Pastikan ID menggunakan awalan T dan input berupa transaksi keuangan.")
                
        except ValueError:
            bot.reply_to(message, "❌ Format ID salah. Contoh yang benar: `T-10`", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Terjadi kesalahan sistem: {str(e)}")