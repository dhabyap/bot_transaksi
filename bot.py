import telebot
import signal
import sys
from config import BOT_TOKEN
import database
from handlers import register_all_handlers
from error_notifier import setup_global_error_handler, notify_error
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize scheduler
scheduler = BackgroundScheduler(timezone="Asia/Jakarta")

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

def daily_reminder_job():
    """Job scheduler untuk mengingatkan user setiap sore/malam."""
    print("[scheduler] Mengirimkan pengingat harian ke semua user...")
    pesan = "👋 *Halo semuanya!*\nJangan lupa ya isi transaksi kalian hari ini agar keuangan makin rapi! 📊"
    broadcast_message(pesan)

def daily_recap_job():
    """Job scheduler untuk mengirimkan rekap harian jam 20:00 ke semua user."""
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    print(f"[scheduler] Mengirimkan rekap harian ({today}) ke semua user...")
    
    user_ids = database.get_all_user_chat_ids()
    for uid in user_ids:
        try:
            data = database.get_daily_summary_per_user(uid, today)
            # Hanya kirim jika ada transaksi hari ini (minimal ada pengeluaran/pemasukan/investasi > 0)
            if data['pengeluaran'] > 0 or data['pemasukan'] > 0 or data['investasi'] > 0:
                pesan = (
                    f"📊 *Rekap Hari Ini — {date.today().strftime('%d %B %Y')}*\n\n"
                    f"💸 Pengeluaran : Rp {data['pengeluaran']:,.0f}\n"
                    f"💰 Pemasukan   : Rp {data['pemasukan']:,.0f}\n"
                    f"📦 Investasi   : Rp {data['investasi']:,.0f}\n\n"
                    f"Selamat beristirahat! Jangan lupa catat transaksi yang terlewat ya. 🌙"
                )
                bot.send_message(uid, pesan, parse_mode='Markdown')
        except Exception as e:
            print(f"  Gagal kirim rekap harian ke {uid}: {e}")

def weekly_recap_job():
    """Job scheduler untuk mengirimkan rekap mingguan setiap Minggu jam 19:00."""
    from datetime import date, timedelta
    today = date.today()
    start_date = (today - timedelta(days=6)).strftime("%Y-%m-%d") # Senin s/d Minggu
    end_date = today.strftime("%Y-%m-%d")
    
    print(f"[scheduler] Mengirimkan rekap mingguan ({start_date} s/d {end_date}) ke semua user...")
    
    user_ids = database.get_all_user_chat_ids()
    for uid in user_ids:
        try:
            data = database.get_weekly_summary_per_user(uid, start_date, end_date)
            # Hanya kirim jika ada pengeluaran minggu ini
            if data['total_pengeluaran'] > 0:
                pesan = (
                    f"📅 *Rekap Minggu Ini*\n"
                    f"({date.today() - timedelta(days=6):%d %b} - {date.today():%d %b %Y})\n\n"
                    f"Total pengeluaran: *Rp {data['total_pengeluaran']:,.0f}*\n"
                    f"Kategori terboros: *{data['top_kategori']}* (Rp {data['top_kategori_nominal']:,.0f})\n\n"
                    f"Yuk, siap-siap atur strategi buat minggu depan! 💪"
                )
                bot.send_message(uid, pesan, parse_mode='Markdown')
        except Exception as e:
            print(f"  Gagal kirim rekap mingguan ke {uid}: {e}")

def shutdown_handler(signum, frame):
    """Handler saat bot dimatikan (CTRL+C / SIGTERM)."""
    print("\n[bot] Mematikan bot, mengirim notifikasi ke semua user...")
    try:
        if scheduler.running:
            scheduler.shutdown()
    except Exception as e:
        print(f"Error shutting down scheduler: {e}")
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

    # Mulai scheduler harian
    scheduler.add_job(daily_reminder_job, 'cron', hour=17, minute=0)
    scheduler.add_job(daily_recap_job, 'cron', hour=20, minute=0)
    scheduler.add_job(weekly_recap_job, 'cron', day_of_week='sun', hour=19, minute=0)
    scheduler.start()
    print("[bot] Scheduler started (Daily reminder at 17:00 WIB)")

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

