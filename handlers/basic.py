import database
from datetime import datetime

def register_handlers(bot):
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

    @bot.message_handler(commands=['profile'])
    def send_profile(message):
        database.upsert_user(message.from_user)
        user_id = message.from_user.id
        profile = database.get_user_profile(user_id)
        
        if not profile:
            bot.reply_to(message, "❌ Profil tidak ditemukan.")
            return
            
        first_name = profile.get("first_name", "")
        username = profile.get("username", "-")
        first_seen = profile.get("first_seen")
        last_active = profile.get("last_active")
        msg_count = profile.get("message_count", 0)
        
        fs_str = first_seen.strftime("%d %b %Y %H:%M") if first_seen else "-"
        la_str = last_active.strftime("%d %b %Y %H:%M") if last_active else "-"
        
        profile_text = (
            f"👤 *Profil Pengguna*\n\n"
            f"🔹 *Nama:* {first_name}\n"
            f"🔹 *Username:* @{username}\n"
            f"🔹 *ID:* `{user_id}`\n\n"
            f"📊 *Statistik*\n"
            f"💬 *Jumlah Pesan:* {msg_count} pesan\n"
            f"📅 *Pertama Kali Menggunakan:* {fs_str}\n"
            f"⏱ *Terakhir Aktif:* {la_str}"
        )
        bot.reply_to(message, profile_text, parse_mode='Markdown')
