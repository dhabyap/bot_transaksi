# Version: 1.1.0
"""
error_notifier.py
=================
Modul untuk mengirim notifikasi error/bug secara otomatis ke admin via Telegram.

Cara kerja:
- Setiap exception yang tidak tertangani (unhandled) akan ditangkap oleh `setup_global_error_handler()`
- Error dikirim langsung ke chat ID admin yang sudah dikonfigurasi di .env
- Menggunakan requests (pure HTTP) agar tidak bergantung pada instance bot yang mungkin sedang error

Penggunaan:
    from error_notifier import setup_global_error_handler, notify_error
    setup_global_error_handler()   # Pasang di awal bot.py
    notify_error("pesan error manual")  # Kirim error manual
"""

import sys
import os
import traceback
import requests
from datetime import datetime

# ─── Ambil konfigurasi dari environment ──────────────────────────────────────
# Menggunakan ERROR_BOT_TOKEN (bot laporan) jika ada, jika tidak fallback ke bot utama
BOT_TOKEN     = os.getenv("ERROR_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def notify_error(message: str, title: str = "🐛 Bug / Error Terdeteksi") -> bool:
    """
    Kirim pesan error ke Telegram admin.

    Args:
        message (str): Isi pesan error / traceback.
        title   (str): Judul pesan (default: 🐛 Bug / Error Terdeteksi).

    Returns:
        bool: True jika berhasil terkirim, False jika gagal.
    """
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        print("[error_notifier] WARNING: TELEGRAM_BOT_TOKEN atau ADMIN_CHAT_ID belum diset di .env")
        return False

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = (
        f"*{title}*\n"
        f"🕐 Waktu: `{timestamp}`\n\n"
        f"```\n{message[:3500]}\n```"  # Batasi panjang agar tidak melebihi limit Telegram (4096 char)
    )

    try:
        response = requests.post(
            TELEGRAM_API_URL,
            data={
                "chat_id": ADMIN_CHAT_ID,
                "text": full_message,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        if response.status_code == 200:
            print(f"[error_notifier] ✅ Error berhasil dikirim ke admin (chat_id: {ADMIN_CHAT_ID})")
            return True
        else:
            print(f"[error_notifier] ❌ Gagal kirim error. Status: {response.status_code} | Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("[error_notifier] ❌ Tidak ada koneksi internet. Error tidak bisa dikirim ke Telegram.")
        return False
    except Exception as e:
        print(f"[error_notifier] ❌ Exception saat notify_error: {e}")
        return False


def _global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Handler global untuk menangkap semua unhandled exception.
    Dipasang ke sys.excepthook agar otomatis aktif.
    """
    # Abaikan KeyboardInterrupt (Ctrl+C) agar tidak dikirim ke Telegram
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Format traceback lengkap
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_string = "".join(tb_lines)

    # Print ke terminal seperti biasa
    print("".join(tb_string))

    # Kirim ke Telegram
    notify_error(tb_string, title="🚨 Unhandled Exception di Bot")


def setup_global_error_handler():
    """
    Pasang global error handler ke sys.excepthook.
    Panggil sekali saja di awal bot.py (sebelum infinity_polling).

    Contoh:
        from error_notifier import setup_global_error_handler
        setup_global_error_handler()
    """
    sys.excepthook = _global_exception_handler
    print("[error_notifier] ✅ Global error handler aktif — error akan dikirim ke Telegram admin.")
