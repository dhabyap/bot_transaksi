# Feature Request: Daily Transaction Reminder

## Description
Menambahkan fungsionalitas pengingat (reminder) otomatis kepada user untuk mencatat atau mengisi transaksi mereka.

## Detail Kebutuhan
- **Waktu Pengiriman:** Sore atau malam hari setiap harinya (misal: 17:00 atau 20:00).
- **Isi Pesan:** Pesan sapaan santai dan ramah sebagai alarm, misalnya: _"Jangan lupa ya isi transaksi kalian hari ini!"_
- **Target:** Mengirimkan pesan kepada seluruh user yang terdaftar atau ke dalam grup (menyesuaikan dengan sistem yang ada).

## Tujuan Misi
Sebagai fitur pengingat (reminder) agar user lebih disiplin dan rutin mencatat transaksi/keuangan mereka setiap harinya.

## Saran Implementasi Teknikal
1. **Scheduler Library:** Menggunakan library seperti `APScheduler` (karena bot dibuat dengan Python) untuk mengatur jadwal pengiriman pesan secara otomatis setiap harinya.
2. **Fetch User:** Membuat query ke database (`finance_bot.db`) untuk mengambil daftar `user_id` atau `chat_id` agar bot bisa melakukan broadcast.
3. **Handler Pesan:** Menambahkan method/handler baru pada struktur bot (misal di dalam `bot.py` atau terpisah di folder `handlers/`) untuk menangani _cron job_ ini.
