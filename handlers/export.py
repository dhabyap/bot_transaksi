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

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import database
from config import MONTH_NAMES


# ── Excel Builder (standalone, tanpa Flask) ────────────────────────────────────

def _build_excel(transactions, user_label: str, period_label: str) -> io.BytesIO:
    """Buat file Excel (.xlsx) dan kembalikan sebagai BytesIO buffer."""
    wb = openpyxl.Workbook()

    # Styles
    header_fill      = PatternFill("solid", fgColor="1C1F2E")
    pemasukan_fill   = PatternFill("solid", fgColor="D1FAE5")
    pengeluaran_fill = PatternFill("solid", fgColor="FEE2E2")
    investasi_fill   = PatternFill("solid", fgColor="DBEAFE")
    thin   = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def hdr_font():
        return Font(name="Calibri", bold=True, color="FFFFFF", size=10)

    def body_font():
        return Font(name="Calibri", size=10)

    # ── Sheet 1: Transaksi ─────────────────────────────────────────────────────
    ws = wb.active
    ws.title = "Transaksi"

    # Baris judul
    ws.merge_cells("A1:I1")
    c = ws["A1"]
    c.value     = f"Laporan Keuangan — {user_label} | {period_label}"
    c.font      = Font(name="Calibri", bold=True, size=13, color="1C1F2E")
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    ws.merge_cells("A2:I2")
    g = ws["A2"]
    g.value     = f"Dibuat: {datetime.now().strftime('%d %B %Y, %H:%M')} via Telegram Bot"
    g.font      = Font(name="Calibri", italic=True, size=9, color="888888")
    g.alignment = Alignment(horizontal="center")

    # Header kolom
    headers = ["No", "ID", "Tanggal & Waktu", "Tipe",
               "Item / Keterangan", "Kategori", "Nominal (Rp)"]
    for ci, h in enumerate(headers, 1):
        cell            = ws.cell(row=4, column=ci, value=h)
        cell.fill       = header_fill
        cell.font       = hdr_font()
        cell.alignment  = Alignment(horizontal="center", vertical="center")
        cell.border     = border
    ws.row_dimensions[4].height = 20
    ws.freeze_panes = "A5"

    tipe_fill_map = {
        "pemasukan":   pemasukan_fill,
        "pengeluaran": pengeluaran_fill,
        "investasi":   investasi_fill,
    }

    for row_no, tx in enumerate(transactions, 1):
        r        = row_no + 4
        tipe_str = (tx.get("tipe") or "").lower()
        fill     = tipe_fill_map.get(tipe_str)

        ts     = tx.get("timestamp")
        ts_str = ts.strftime("%d/%m/%Y %H:%M") if ts else "-"
        nom    = tx.get("nominal") or 0

        row_data = [
            row_no,
            f"T-{tx.get('id', '')}",
            ts_str,
            tipe_str.capitalize() or "-",
            tx.get("item") or "-",
            (tx.get("kategori") or "-").replace("_", " ").capitalize(),
            nom,
        ]

        for ci, val in enumerate(row_data, 1):
            cell        = ws.cell(row=r, column=ci, value=val)
            cell.border = border
            cell.font   = body_font()
            if fill:
                cell.fill = fill
            if ci == 7:   # Nominal
                cell.alignment    = Alignment(horizontal="right")
                cell.number_format = "#,##0"
            elif ci == 1:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Lebar kolom
    col_widths = [5, 10, 20, 15, 35, 20, 20]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ── Sheet 2: Ringkasan ─────────────────────────────────────────────────────
    ws2 = wb.create_sheet("Ringkasan")
    ws2.column_dimensions["A"].width = 32
    ws2.column_dimensions["B"].width = 22

    t = ws2.cell(row=1, column=1, value="Ringkasan Keuangan")
    t.font      = Font(name="Calibri", bold=True, size=13, color="1C1F2E")
    ws2.merge_cells("A1:B1")
    t.alignment = Alignment(horizontal="center")
    ws2.row_dimensions[1].height = 24

    ws2.cell(row=2, column=1, value="Periode").font = Font(bold=True, size=9, color="888888")
    ws2.cell(row=2, column=2, value=f"{user_label} | {period_label}").font = Font(size=9, color="888888")

    pemasukan   = sum(t.get("nominal", 0) or 0 for t in transactions if (t.get("tipe") or "").lower() == "pemasukan")
    pengeluaran = sum(t.get("nominal", 0) or 0 for t in transactions if (t.get("tipe") or "").lower() == "pengeluaran")
    investasi   = sum(t.get("nominal", 0) or 0 for t in transactions if (t.get("tipe") or "").lower() == "investasi")
    saldo_cash   = pemasukan - pengeluaran
    saldo_bersih = pemasukan - pengeluaran - investasi

    rows_summary = [
        ("Total Pemasukan",              pemasukan,   "3D9970"),
        ("Total Pengeluaran",            pengeluaran,  "E74C3C"),
        ("Total Investasi / Tabungan",   investasi,    "3498DB"),
        ("Saldo Cash (Pem. − Peng.)",    saldo_cash,   "2C3E50"),
        ("Saldo Bersih (inc. Investasi)", saldo_bersih,"8E44AD"),
    ]
    for ridx, (label, val, color) in enumerate(rows_summary, 4):
        lc        = ws2.cell(row=ridx, column=1, value=label)
        lc.font   = Font(name="Calibri", bold=True, size=10, color=color)
        lc.border = border
        vc              = ws2.cell(row=ridx, column=2, value=val)
        vc.font         = Font(name="Calibri", size=10)
        vc.border       = border
        vc.number_format = "#,##0"
        vc.alignment    = Alignment(horizontal="right")

    ws2.cell(row=10, column=1, value="Total Transaksi").font = Font(bold=True, size=10)
    wc = ws2.cell(row=10, column=2, value=len(transactions))
    wc.font      = Font(size=10)
    wc.alignment = Alignment(horizontal="center")

    # Simpan ke buffer
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


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
            buf = _build_excel(transactions, first_name, period_label)
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

        pemasukan   = sum(t.get("nominal", 0) or 0 for t in transactions if (t.get("tipe") or "").lower() == "pemasukan")
        pengeluaran = sum(t.get("nominal", 0) or 0 for t in transactions if (t.get("tipe") or "").lower() == "pengeluaran")
        investasi   = sum(t.get("nominal", 0) or 0 for t in transactions if (t.get("tipe") or "").lower() == "investasi")
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
