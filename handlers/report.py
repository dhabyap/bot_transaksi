from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import calendar
from datetime import datetime
import database
from config import MONTH_NAMES

def register_handlers(bot):
    def generate_report_text(report, month, year):
        pemasukan = report.get('pemasukan', 0) or 0
        pengeluaran = report.get('pengeluaran', 0) or 0
        investasi = report.get('investasi', 0) or 0 # Tambahan: Tarik data investasi
        
        # Saldo = Uang yang masuk dikurangi pengeluaran dan uang yang diinvestasikan
        saldo = pemasukan - pengeluaran - investasi
        
        month_name = MONTH_NAMES.get(month, "")
        last_day = calendar.monthrange(year, month)[1]
        
        report_text = (
            f"📊 *Laporan Keuangan*\n"
            f"🗓 *Periode:* 1 {month_name} {year} - {last_day} {month_name} {year}\n\n"
            f"🟢 Pemasukan: Rp {pemasukan:,.0f}\n"
            f"🔴 Pengeluaran: Rp {pengeluaran:,.0f}\n"
            f"🔵 Investasi/Tabungan: Rp {investasi:,.0f}\n" # Tampilkan investasi
            "-------------------------\n"
            f"⚖️ Sisa Saldo (Cash): Rp {saldo:,.0f}"
        )
        return report_text

    def get_report_markup(month, year):
        markup = InlineKeyboardMarkup()
        
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
            
        next_month = month + 1
        next_year = year
        if next_month == 13:
            next_month = 1
            next_year += 1
            
        btn_prev = InlineKeyboardButton("⬅️ Bulan Sebelumnya", callback_data=f"report_{prev_month}_{prev_year}")
        btn_next = InlineKeyboardButton("Bulan Berikutnya ➡️", callback_data=f"report_{next_month}_{next_year}")
        
        markup.row(btn_prev, btn_next)
        return markup

    @bot.message_handler(commands=['laporan'])
    def send_report(message):
        database.upsert_user(message.from_user)
        user_id = message.from_user.id
        
        now = datetime.now()
        month = now.month
        year = now.year
        month_str = f"{year}-{month:02d}"
        
        report = database.get_monthly_report(user_id, month_str)
        
        report_text = generate_report_text(report, month, year)
        markup = get_report_markup(month, year)
        
        bot.reply_to(message, report_text, parse_mode='Markdown', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('report_'))
    def callback_report(call):
        # PENTING: Hentikan animasi loading di tombol Telegram
        bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        _, month_str, year_str = call.data.split('_')
        month = int(month_str)
        year = int(year_str)
        target_month_str = f"{year}-{month:02d}"
        
        report = database.get_monthly_report(user_id, target_month_str)
        
        report_text = generate_report_text(report, month, year)
        markup = get_report_markup(month, year)
        
        # Gunakan try-except untuk mencegah error jika teks yang diedit sama persis dengan sebelumnya
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text=report_text, 
                parse_mode='Markdown', 
                reply_markup=markup
            )
        except Exception as e:
            pass # Abaikan jika error karena pesan tidak ada perubahan

    @bot.message_handler(commands=['riwayat'])
    def send_history(message):
        database.upsert_user(message.from_user)
        user_id = message.from_user.id
        history = database.get_history(user_id) # Asumsi: history mengembalikan 10-20 transaksi terakhir
        
        if not history:
            bot.reply_to(message, "📭 Belum ada riwayat keuangan.", parse_mode='Markdown')
            return
            
        text = "📜 *Riwayat Keuangan Terbaru:*\n\n"
        for item in history:
            item_id = item['id']
            tipe = item.get('tipe', 'pengeluaran') # pemasukan, pengeluaran, investasi
            kategori = item.get('kategori', 'lainnya').replace('_', ' ').capitalize()
            name = item['item']
            val = item['val']
            timestamp = item.get('timestamp')
            date_str = timestamp.strftime('%d/%m %H:%M') if timestamp else "-"
            
            # Sesuaikan emoji berdasarkan tipe arus kas
            if tipe == 'pemasukan':
                icon = "🟢"
            elif tipe == 'investasi':
                icon = "🔵"
            else:
                icon = "🔴"
                
            text += f"{icon} `[{date_str}]` `[ID:{item_id}]`\n*{name}* (Rp {val:,.0f})\n_Kategori: {kategori}_\n\n"
                
        text += "💡 *Tips:* Gunakan `/hapus <ID>` jika ada transaksi yang salah catat."
        bot.reply_to(message, text, parse_mode='Markdown')