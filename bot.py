import telebot
import signal
import sys
from config import BOT_TOKEN
import database
from handlers import register_all_handlers
from error_notifier import setup_global_error_handler, notify_error

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize database
database.init_db()

# Register all handlers from the modular architecture
register_all_handlers(bot)

def broadcast_message(text):
    """Kirim pesan ke semua user yang terdaftar di database."""
    try:
        user_ids = database.get_all_user_chat_ids()
        for uid in user_ids:
            try:
                bot.send_message(uid, text, parse_mode='Markdown')
            except Exception as e:
                print(f"  Gagal kirim ke {uid}: {e}")
        print(f"[broadcast] Pesan terkirim ke {len(user_ids)} user.")
    except Exception as e:
        print(f"[broadcast] Error: {e}")

def shutdown_handler(signum, frame):
    """Handler saat bot dimatikan (CTRL+C / SIGTERM)."""
    print("\n[bot] Mematikan bot, mengirim notifikasi ke semua user...")
    broadcast_message("🔴 *Bot mati!*\nLaptop Yuhu sedang offline. Bot tidak dapat menerima pesan sementara.")
    sys.exit(0)

if __name__ == "__main__":
    # ─── Aktifkan notifikasi error ke Telegram admin ────────────────────────
    setup_global_error_handler()

    # Setup auto-suggest / menu perintah di Telegram
    bot.set_my_commands([
        telebot.types.BotCommand("/start",   "Menjalankan ulang / info bot"),
        telebot.types.BotCommand("/help",    "Info cara penggunaan bot"),
        telebot.types.BotCommand("/laporan", "Ringkasan keuangan bulanan"),
        telebot.types.BotCommand("/riwayat", "Riwayat transaksi terakhir"),
        telebot.types.BotCommand("/export",  "Download Excel transaksi ke chat"),
        telebot.types.BotCommand("/profile", "Lihat profil & statistik"),
        telebot.types.BotCommand("/edit",    "Edit transaksi: /edit <ID> <teks>"),
        telebot.types.BotCommand("/hapus",   "Hapus transaksi: /hapus <ID>"),
    ])

    # Daftarkan handler shutdown (CTRL+C / kill signal)
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    print("Bot is running...")

    # Kirim notifikasi ke semua user bahwa bot sudah nyala
    broadcast_message("🟢 *Bot transaksi AI sudah nyala!*\nLaptop Yuhu sedang online. Bot siap menerima pesan kamu.")

    try:
        bot.infinity_polling()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[bot] ❌ Bot mati karena exception:\n{tb}")
        notify_error(tb, title="🚨 Bot Mati — Crash saat Polling")
        sys.exit(1)

