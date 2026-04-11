import database
from datetime import datetime
from telebot import types

def register_handlers(bot):
    def get_welcome_text():
        return (
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
            "👤 /profile - Lihat profil & statistik\n\n"
            "📥 *Export Excel:*\n"
            "📊 /export - Excel bulan ini\n"
            "📊 /export `2026-03` - Excel bulan tertentu\n"
            "📊 /export `all` - Semua transaksi (semua bulan)"
        )

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        database.upsert_user(message.from_user)
        user_id = message.from_user.id
        
        # Cek status disclaimer
        if not database.get_disclaimer_status(user_id):
            disclaimer_text = (
                "⚠️ *Perhatian Penting!*\n\n"
                "Bot ini masih dalam tahap *Experimental* 🧪\n\n"
                "Selama penggunaan, Anda mungkin akan menerima beberapa notifikasi otomatis, "
                "pengingat harian, dan pesan lainnya yang mungkin terasa seperti spam. "
                "Kami sedang terus melakukan pengembangan dan mohon maaf atas ketidaknyamanan ini.\n\n"
                "Silakan tekan tombol di bawah jika Anda setuju untuk melanjutkan."
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Saya Mengerti & Lanjutkan", callback_data="accept_disclaimer"))
            bot.reply_to(message, disclaimer_text, parse_mode='Markdown', reply_markup=markup)
            return

        bot.reply_to(message, get_welcome_text(), parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data == "accept_disclaimer")
    def handle_disclaimer_acceptance(call):
        user_id = call.from_user.id
        database.update_disclaimer_status(user_id, 1)
        
        # Beri feedback & hapus pesan disclaimer, ganti dengan welcome message
        bot.answer_callback_query(call.id, "Terima kasih! Selamat menggunakan bot.")
        
        # Edit pesan disclaimer menjadi welcome message
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=get_welcome_text(),
            parse_mode='Markdown'
        )

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