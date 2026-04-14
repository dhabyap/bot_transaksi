import io
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from utils.excel_builder import build_excel
import database
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_finance_bot_2024"

# Custom Jinja2 filter: parse JSON string di template
app.jinja_env.filters['from_json'] = json.loads

# Inisialisasi database MySQL saat aplikasi web mulai jalan
try:
    database.init_db()
except Exception as e:
    print(f"Gagal menginisialisasi database: {e}")


# ─── Helper ───────────────────────────────────────────────────────────────────

def _parse_filters(request):
    """Ambil month dan user_id filter dari query string."""
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    user_id_filter = request.args.get('user_id', '')
    uid = int(user_id_filter.strip()) if user_id_filter.strip().isdigit() else None
    return month, user_id_filter, uid


def _build_daily_chart_data(daily_trend, month_str):
    """
    Ubah hasil get_daily_trend menjadi dict berisi label + datasets
    yang siap di-serialize ke JSON untuk Chart.js.
    """
    # Tentukan jumlah hari dalam bulan
    year, month = map(int, month_str.split('-'))
    import calendar
    total_days = calendar.monthrange(year, month)[1]
    labels = list(range(1, total_days + 1))

    pemasukan_map  = {row['day']: float(row['total']) for row in daily_trend if row['tipe'] == 'pemasukan'}
    pengeluaran_map = {row['day']: float(row['total']) for row in daily_trend if row['tipe'] == 'pengeluaran'}
    investasi_map  = {row['day']: float(row['total']) for row in daily_trend if row['tipe'] == 'investasi'}

    return {
        'labels': labels,
        'pemasukan':   [pemasukan_map.get(d, 0)   for d in labels],
        'pengeluaran': [pengeluaran_map.get(d, 0) for d in labels],
        'investasi':   [investasi_map.get(d, 0)   for d in labels],
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    month, user_id_filter, uid = _parse_filters(request)

    try:
        transactions  = database.get_transactions_by_month(month, uid)
        report        = database.get_monthly_report(uid, month)
        all_users     = database.get_all_users()
        category_data = database.get_category_breakdown(month, uid)
        daily_trend   = database.get_daily_trend(month, uid)
        stats         = database.get_stats_summary(month, uid)

        pemasukan   = float(report.get('pemasukan') or 0)
        pengeluaran = float(report.get('pengeluaran') or 0)
        investasi   = float(report.get('investasi') or 0)

    except Exception as e:
        print(f"Error accessing database in dashboard: {e}")
        flash("Terjadi kesalahan saat mengakses data dari database.", "error")
        transactions  = []
        all_users     = []
        category_data = []
        daily_trend   = []
        stats         = {'total_tx': 0, 'avg_daily_pengeluaran': 0, 'top_category': '-', 'top_category_val': 0}
        pemasukan = pengeluaran = investasi = 0.0

    # Kalkulasi saldo
    saldo_cash   = pemasukan - pengeluaran          # uang cash fisik
    saldo_bersih = pemasukan - pengeluaran - investasi  # termasuk investasi

    # Siapkan data chart sebagai JSON string agar aman di-inject ke JS
    pie_chart = {
        'labels': [row['kategori'] for row in category_data],
        'data':   [float(row['total']) for row in category_data],
    }
    daily_chart = _build_daily_chart_data(daily_trend, month)

    return render_template(
        'index.html',
        # Data transaksi
        transactions=transactions,
        all_users=all_users,
        # Filter state
        month=month,
        user_id_filter=user_id_filter,
        # Kartu ringkasan
        pemasukan=pemasukan,
        pengeluaran=pengeluaran,
        investasi=investasi,
        saldo_cash=saldo_cash,
        saldo_bersih=saldo_bersih,
        # Statistik
        stats=stats,
        # Chart data (JSON string)
        pie_chart_json=json.dumps(pie_chart),
        daily_chart_json=json.dumps(daily_chart),
    )


@app.route('/delete/<int:tx_id>', methods=['POST'])
def delete_tx(tx_id):
    """Dashboard adalah halaman admin — boleh hapus transaksi siapapun."""
    try:
        success = database.admin_delete_transaction(tx_id)
        if success:
            flash("✅ Data transaksi berhasil dihapus!", "success")
        else:
            flash("❌ Data transaksi tidak ditemukan.", "error")
    except Exception as e:
        print(f"Error in dashboard deletion: {e}")
        flash("Terjadi kesalahan sistem saat menghapus data.", "error")

    return redirect(request.referrer or url_for('index'))




@app.route('/export/excel')
def export_excel():
    """
    Export Excel transaksi.
    Query params opsional: month (YYYY-MM), user_id (angka).
    Contoh: /export/excel?month=2026-04&user_id=123456789
    """
    # Ambil filter dari query string (sama persis dengan filter utama)
    month_str, user_id_filter, uid = _parse_filters(request)

    # Tentukan label untuk nama file & judul sheet
    user_label  = "Semua User"
    month_label = month_str

    if uid:
        all_users = database.get_all_users()
        matched = next((u for u in all_users if u["user_id"] == uid), None)
        if matched:
            nama = matched["first_name"] or ""
            if matched.get("last_name"):
                nama += " " + matched["last_name"]
            user_label = nama.strip() or str(uid)

    try:
        transactions = database.get_all_transactions_export(month_str=month_str, user_id=uid)
    except Exception as e:
        print(f"Error in dashboard export: {e}")
        flash("Gagal mengambil data transaksi untuk export.", "error")
        return redirect(url_for('index'))

    wb = build_excel(transactions, user_label, month_label, include_user_info=True)

    # Simpan ke buffer memori
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    safe_user  = user_label.replace(" ", "_").replace("/", "-")
    filename   = f"transaksi_{safe_user}_{month_label}.xlsx"

    return send_file(
        buf,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == '__main__':
    app.run(debug=True, port=5000)
