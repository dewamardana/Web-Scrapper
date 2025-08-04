# Web-Scrapper
A Python scraper to extract health articles from Halodoc and Alodokter using Selenium and BeautifulSoup. Retrieves title, author, publish date, content, tags, and links. For research and educational use only. All content belongs to the respective websites—do not use commercially without permission.


📰 Artikel Scraper Halodoc & Alodokter
Python-based web scraper untuk mengambil artikel kesehatan dari dua situs populer di Indonesia: Halodoc dan Alodokter. Data yang dikumpulkan mencakup:

Judul artikel

Penulis atau peninjau

Tanggal publikasi

Isi artikel lengkap

Tag artikel

Sumber dan link artikel

Data disimpan dalam format JSON per sumber dan kata kunci pencarian.

📅 Kapan Digunakan?
Scraper ini cocok digunakan untuk:

Riset konten kesehatan

Pengumpulan data untuk NLP atau analisis teks

Studi banding topik medis

Dataset pendidikan dan akademik (bukan untuk produksi tanpa izin resmi dari situs sumber)

⚙️ Fitur
Menggunakan Selenium dan BeautifulSoup untuk scraping halaman dinamis.

Mendukung pencarian berbasis kata kunci (keyword).

Bisa menentukan jumlah artikel yang ingin dikumpulkan.

Scraping dari dua situs sekaligus:

halodoc.com

alodokter.com

Penanganan error & retry otomatis jika gagal mengambil artikel.

🚀 Instalasi dan Cara Menjalankan
1. Clone Repository
bash
Copy
Edit
git clone https://github.com/username/nama-repo.git
cd nama-repo
2. Buat dan Aktifkan Virtual Environment (opsional tapi disarankan)
bash
Copy
Edit
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
4. Jalankan Scraper
bash
Copy
Edit
python main.py
Kemudian masukkan:

Kata kunci pencarian: contoh mental, diabetes, dll.

Jumlah artikel: angka (misal 10) atau ketik max untuk semua yang tersedia.

📁 Output
File hasil scraping disimpan otomatis ke dalam folder:

pgsql
Copy
Edit
Data/
  ├── halodoc.com/
  │     └── mental.json
  └── alodokter.com/
        └── mental.json
Format output:

json
Copy
Edit
[
  {
    "judul_artikel": "Apa Itu Kesehatan Mental?",
    "penulis_peninjau": "dr. Andi",
    "tanggal_publish": "10 Agustus 2023",
    "isi_artikel": "...",
    "tag": ["Psikologi", "Mental"],
    "link": "https://www.halodoc.com/artikel/apa-itu-kesehatan-mental",
    "sumber_data": "halodoc.com"
  }
]
✅ Requirements
Lihat requirements.txt, tapi secara umum kamu butuh:

Python >= 3.8

Google Chrome terinstal

ChromeDriver versi kompatibel dengan Chrome

Library:

requests

beautifulsoup4

selenium

💡 Tips
Untuk kemudahan setup ChromeDriver, kamu bisa menambahkan webdriver-manager dan mengganti inisialisasi Selenium.

File HTML debug disimpan secara otomatis untuk membantu saat gagal mengambil elemen.

⚠️ Disclaimer
Proyek ini hanya untuk tujuan edukasi dan riset pribadi. Semua konten milik Halodoc dan Alodokter. Jangan gunakan untuk kepentingan komersial tanpa izin dari sumber resmi.
