import database
from ai_brain import get_json_data_from_text

def register_handlers(bot):
    @bot.message_handler(commands=['hapus'])
    def delete_item(message):
        database.upsert_user(message.from_user)
        user_id = message.from_user.id
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Format salah. Gunakan: `/hapus <ID>`\nContoh: `/hapus 10` atau `/hapus T-10`", parse_mode='Markdown')
            return
            
        raw_id = parts[1].upper()
        try:
            # Support both plain number (e.g. 27) and prefixed format (e.g. T-27)
            if raw_id.isdigit():
                item_id = int(raw_id)
                display_id = f"T-{item_id}"
            elif '-' in raw_id:
                prefix, id_part = raw_id.split('-', 1)
                item_id = int(id_part)
                if prefix != 'T':
                    bot.reply_to(message, "❌ ID tidak valid. Gunakan angka (contoh: `27`) atau awalan T (contoh: `T-27`).", parse_mode='Markdown')
                    return
                display_id = raw_id
            else:
                raise ValueError("Format tidak dikenali")
            
            success = database.delete_transaction(item_id, user_id)
            if success:
                bot.reply_to(message, f"✅ Data `{display_id}` berhasil dihapus.", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"❌ Data `{display_id}` tidak ditemukan atau bukan milik Anda.")
                
        except ValueError:
            bot.reply_to(message, "❌ Format ID salah. Gunakan angka (contoh: `/hapus 27`) atau format T (contoh: `/hapus T-10`)", parse_mode='Markdown')

    @bot.message_handler(commands=['edit'])
    def edit_item(message):
        database.upsert_user(message.from_user)
        user_id = message.from_user.id
        # Gunakan maxsplit=2 agar kalimat baru tidak terpotong-potong
        parts = message.text.split(maxsplit=2) 
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ Format salah. Gunakan: `/edit <ID> <Kalimat Baru>`\nContoh: `/edit 10 gaji naik 5 juta` atau `/edit T-10 gaji naik 5 juta`", parse_mode='Markdown')
            return
            
        raw_id = parts[1].upper()
        new_text = parts[2]
        
        bot.send_chat_action(message.chat.id, 'typing')
        data = get_json_data_from_text(new_text)
        
        if data.get("error"):
            bot.reply_to(message, "❌ Gagal memproses kalimat baru. Pastikan formatnya jelas dan terkait keuangan.")
            return
            
        try:
            # Support both plain number (e.g. 10) and prefixed format (e.g. T-10)
            if raw_id.isdigit():
                item_id = int(raw_id)
                display_id = f"T-{item_id}"
            elif '-' in raw_id:
                prefix, id_part = raw_id.split('-', 1)
                item_id = int(id_part)
                if prefix != 'T':
                    bot.reply_to(message, "❌ ID tidak valid. Gunakan angka (contoh: `10`) atau awalan T (contoh: `T-10`).", parse_mode='Markdown')
                    return
                display_id = raw_id
            else:
                raise ValueError("Format tidak dikenali")
            
            tipe = data.get("tipe", "").lower()
            item_name = data.get("item", "")
            nominal = float(data.get("nominal", 0))
            kategori = data.get("kategori", "")
            
            if tipe in ["pemasukan", "pengeluaran", "investasi"]:
                success = database.update_transaction(item_id, user_id, tipe, item_name, nominal, kategori)
                
                if success:
                    feedback = (
                        f"✅ Data `{display_id}` berhasil diperbarui:\n\n"
                        f"🔹 *Tipe:* {tipe.capitalize()}\n"
                        f"🔹 *Item:* {item_name}\n"
                        f"🔹 *Nominal:* Rp {nominal:,.0f}\n"
                        f"🔹 *Kategori:* {kategori.replace('_', ' ').capitalize()}"
                    )
                    bot.reply_to(message, feedback, parse_mode='Markdown')
                else:
                    bot.reply_to(message, f"❌ Data `{display_id}` tidak ditemukan atau bukan milik Anda.")
            else:
                bot.reply_to(message, "❌ Gagal memperbarui. Pastikan input berupa transaksi keuangan yang valid.")
                
        except ValueError:
            bot.reply_to(message, "❌ Format ID salah. Gunakan angka (contoh: `/edit 10 ...`) atau format T (contoh: `/edit T-10 ...`)", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Terjadi kesalahan sistem: {str(e)}")