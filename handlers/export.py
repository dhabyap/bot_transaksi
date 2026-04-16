"""
Handler /export — Kirim file Excel transaksi langsung ke chat Telegram.

Cara pakai:
  /export               → Excel bulan ini (semua transaksi user)
  /export 2026-03       → Excel bulan tertentu
  /export all           → Semua transaksi user (semua bulan)
"""

import io
import calendar
from datetime import datetime

from openpyxl.utils import get_column_letter

from utils.excel_generator import generate_excel_report
import database
from config import MONTH_NAMES




# ── Telegram Handler ───────────────────────────────────────────────────────────

def register_handlers(bot):

    @bot.message_handler(commands=['export'])
    def export_excel(message):
        """
        /export               → bulan ini
        /export 2026-03       → bulan tertentu (YYYY-MM)
        /export all           → semua bulan
        """
        database.upsert_user(message.from_user)
        user_id    = message.from_user.id
        first_name = message.from_user.first_name or "User"

        parts = message.text.strip().split()
        arg   = parts[1].strip().lower() if len(parts) > 1 else ""

        now = datetime.now()

        # ── Tentukan periode & query ───────────────────────────────────
        if arg == "all":
            # Semua bulan, milik user ini
            period_label = "Semua Periode"
            month_str    = None
        elif arg == "":
            # Default: bulan ini
            month_str    = now.strftime("%Y-%m")
            mn           = MONTH_NAMES.get(now.month, "")
            period_label = f"{mn} {now.year}"
        else:
            # Format YYYY-MM
            try:
                dt = datetime.strptime(arg, "%Y-%m")
                month_str    = arg
                mn           = MONTH_NAMES.get(dt.month, "")
                period_label = f"{mn} {dt.year}"
            except ValueError:
                bot.reply_to(
                    message,
                    "❌ Format bulan tidak valid.\n\n"
                    "Gunakan salah satu format:\n"
                    "• `/export` — bulan ini\n"
                    "• `/export 2026-03` — bulan tertentu\n"
                    "• `/export all` — semua transaksi",
                    parse_mode="Markdown"
                )
                return

        # ── Kirim status "sedang memproses" ───────────────────────────
        bot.send_chat_action(message.chat.id, "upload_document")
        status_msg = bot.reply_to(message, "⏳ Menyiapkan file Excel...")

        # ── Ambil data dari database ───────────────────────────────────
        try:
            transactions = database.get_all_transactions_export(
                month_str=month_str,
                user_id=user_id         # ← hanya data milik user ini
            )
        except Exception as e:
            print(f"Error fetching export data: {e}")
            bot.edit_message_text(
                "❌ Gagal mengambil data transaksi. Silakan coba lagi nanti.",
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )
            return

        if not transactions:
            bot.edit_message_text(
                f"📭 Tidak ada transaksi untuk periode *{period_label}*.\n"
                "Coba bulan lain atau gunakan `/export all`.",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode="Markdown"
            )
            return

        # ── Buat file Excel ────────────────────────────────────────────
        try:
            wb = generate_excel_report(transactions, first_name, period_label, include_user_info=False)
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
        except Exception as e:
            print(f"Error building Excel file: {e}")
            bot.edit_message_text(
                "❌ Gagal membuat file Excel. Silakan coba lagi nanti.",
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )
            return

        # ── Kirim file ke chat ─────────────────────────────────────────
        safe_name    = first_name.replace(" ", "_")
        safe_period  = period_label.replace(" ", "_").replace("/", "-")
        filename     = f"transaksi_{safe_name}_{safe_period}.xlsx"

        pemasukan   = sum(tx.get("nominal", 0) or 0 for tx in transactions if (tx.get("tipe") or "").lower() == "pemasukan")
        pengeluaran = sum(tx.get("nominal", 0) or 0 for tx in transactions if (tx.get("tipe") or "").lower() == "pengeluaran")
        investasi   = sum(tx.get("nominal", 0) or 0 for tx in transactions if (tx.get("tipe") or "").lower() == "investasi")
        saldo_cash  = pemasukan - pengeluaran

        caption = (
            f"📊 *Export Excel Berhasil!*\n\n"
            f"👤 *User:* {first_name}\n"
            f"🗓 *Periode:* {period_label}\n"
            f"📋 *Total Transaksi:* {len(transactions)}\n\n"
            f"🟢 Pemasukan: Rp {pemasukan:,.0f}\n"
            f"🔴 Pengeluaran: Rp {pengeluaran:,.0f}\n"
            f"🔵 Investasi: Rp {investasi:,.0f}\n"
            f"─────────────────────\n"
            f"💵 Saldo Cash: Rp {saldo_cash:,.0f}"
        )

        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass

        bot.send_document(
            chat_id=message.chat.id,
            document=buf,
            visible_file_name=filename,
            caption=caption,
            parse_mode="Markdown"
        )
