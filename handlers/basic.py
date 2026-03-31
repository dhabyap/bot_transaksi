import database
from datetime import datetime

def register_handlers(bot):
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        database.upsert_user(message.from_user)
        
        # Teks disesuaikan murni untuk keuangan pribadi
        welcome_text = (
            "🤖 *Bot Jurnal Keuangan Pribadi*\n\n"
            "Halo! Saya adalah asisten AI pribadimu untuk mencatat arus kas dan mengawal perjalananmu menuju *financial freedom*.\n\n"
            "📝 *Cara Mencatat:*\n"
            "Cukup ketik transaksimu sehari-hari seperti ngobrol biasa. AI akan otomatis memahaminya!\n"
            "• _'Gaji bulan ini 4 juta'_\n"
            "• _'Beli bensin 30rb'_\n"
            "• _'Top up reksadana 500 ribu'_\n\n"
            "🛠 *Perintah Tersedia:*\n"
            "📊 /laporan - Ringkasan keuangan bulanan\n"
            "📜 /riwayat - Lihat riwayat transaksi terakhir\n"
            "✏️ /edit `<ID> <Teks>` - Ubah transaksi\n"
            "🗑 /hapus `<ID>` - Hapus transaksi\n"
            "👤 /profile - Lihat profil & statistik"
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
        
        # Format tanggal agar lebih rapi
        fs_str = first_seen.strftime("%d %b %Y %H:%M") if first_seen else "-"
        la_str = last_active.strftime("%d %b %Y %H:%M") if last_active else "-"
        
        profile_text = (
            f"👤 *Profil Pengguna*\n\n"
            f"🔹 *Nama:* {first_name}\n"
            f"🔹 *Username:* @{username}\n"
            f"🔹 *ID:* `{user_id}`\n\n"
            f"📊 *Statistik Interaksi*\n"
            f"💬 *Jumlah Pesan:* {msg_count} pesan dicatat\n"
            f"📅 *Mulai Menggunakan:* {fs_str}\n"
            f"⏱ *Terakhir Aktif:* {la_str}"
        )
        bot.reply_to(message, profile_text, parse_mode='Markdown')