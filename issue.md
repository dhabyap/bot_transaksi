# Feature Request: Flexible LLM Fallback (Dynamic Model Switching)

## Description
Saat ini bot AI (`ai_brain.py`) sangat bergantung pada ketersediaan tunggal dari **Google Gemini API**. Apabila sewaktu-waktu kuota (_rate limit_) API Key tersebut habis, fitur AI bot tidak akan berfungsi murni.
Oleh karena itu, sistem ini butuh peningkatan dengan menerapkan arsitektur **Dynamic LLM Router**. Router ini akan mengatur lalu lintas API secara lebih cerdas: Jika satu provider limit/error, ia akan meneruskan *prompt* secara *real-time* ke provider alternatif (Fallback) di baliknya.

## Rekomendasi LLM Gratis & Alternatif (Fallback Options)
Sistem ini sebaiknya mengakomodir lebih banyak provider yang menyediakan *free tier* besar atau bahkan gratis sepenuhnya sebagai cadangan:
1. **Google Gemini (Utama):** Model standar yang dipakai saat ini.
2. **Groq API:** Provider dengan prosesing (LPU) tercepat di dunia. Benar-benar gratis untuk menjalankan model seperti **Meta Llama 3**, **Mixtral 8x7B**, dll.
3. **OpenRouter (Agregator):** Platform aggregator yang satu API endpoint-nya bisa mengakses banyak LLM gratis (*free routes*) secara dinamis.
4. **Cohere API:** Memiliki *Developer Tier* gratis dan sangat murah hati yang mendukung bahasa Indonesia via model **Command R / Command R+**.
5. **DeepSeek API:** Alternatif yang sangat powerful dengan tarif *Open Source* yang luar biasa murah, sering digunakan sebagai cadangan terbaik setelah OpenAI/Gemini.
6. **Together AI API:** Alternatif provider yang bisa dibilang gratis di awal, memberi akses ke hampir semua model *open-source*.
7. **HuggingFace Serverless API:** Jika menggunakan model kecil (seperti Mistral 7B / Zephyr), tier gratis reguler HuggingFace juga masih mumpunI.

## Detail Kebutuhan
- **Class Abstraction:** Format standar input *prompt* dan output harus distandarisasi dan dipisahkan dari logik Telegram, agar kita bisa menukar provider dengan mulus.
- **Sistem Prioritas (Routing):** Prioritas provider diatur via daftar antrean panjang di `.env`. Contoh `LLM_FALLBACK_ORDER=gemini,groq,openrouter,cohere`.
- **Deteksi Interupsi yang Presisi:** Bot mampu membedakan error biasa vs error limit (_HTTP 429 Too Many Requests_, atau _Quota Exceeded_) untuk memutuskan kapan harus melakukan _fallback_.

## Tujuan Misi
Target akhirnya adalah **Zero-Downtime AI Analitik**. Bot tidak akan pernah "berhenti menjawab" atau mengirim pesan "Sistem Sedang Gangguan", berkat deretan _sistem cadangan gratis_ tak berujung yang siap menggantikan Gemini.

## Saran Implementasi Teknikal
1. **Library Standardisasi:** Sebagai _hack_ cepat, karena sebagian besar provider besar saat ini (Groq, DeepSeek, Together AI, OpenRouter) meniru standar API OpenAI, kita bisa menggunakan library backend `openai` bawaan Python. Kita cukup memodifikasi parameter `base_url` dan `api_key` nya saja ke masing-masing provider secara bergantian.
2. **Retry Loop Mechanism:** Membuat fungsi generator percobaan bertingkat. Jika `try call(Gemini)` *throws QuotaExhausted*, lompat blocknya ke `try call(Groq)`.
3. Semua kredensial cadangannya (misal: `GROQ_API_KEY`, `COHERE_TOKEN`) diamankan dan dicatatkan formatnya di file `.env.example`.
