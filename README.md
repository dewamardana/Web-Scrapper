# 🕸️ Web Scraper

A Python-based scraper to extract health-related articles from **Halodoc** and **Alodokter** using **Selenium** and **BeautifulSoup**.  
It retrieves the **title, author/reviewer, publish date, full content, tags, and source link**.  
📚 Intended for research and educational use only.  
⚠️ All content belongs to the respective websites. Do not use commercially without proper authorization.

---

## 📰 What It Does

This tool scrapes health articles from two popular Indonesian medical platforms:  
**Halodoc** and **Alodokter**.

### Extracted Information:
- ✅ Article title  
- 👨‍⚕️ Author or reviewer  
- 📅 Publication date  
- 📄 Full article content  
- 🏷️ Article tags  
- 🔗 Source URL  

Results are saved as structured **JSON files**, grouped by source and search keyword.

---

## 📅 When to Use

This scraper is useful for:
- 📚 Health content research  
- 🤖 Data collection for NLP or text analysis  
- 🔍 Comparative studies of medical topics  
- 🎓 Academic and educational datasets  
*(Not intended for production or commercial use without permission.)*

---

## ⚙️ Features

- 🧠 Uses **Selenium** and **BeautifulSoup** to handle dynamic web content  
- 🔍 Keyword-based search  
- 🧾 Choose how many articles to scrape  
- 🌐 Dual-source scraping from:
  - `halodoc.com`  
  - `alodokter.com`  
- 🔁 Automatic retries and error handling  

---

## 🚀 Installation & Usage

### 1. Clone the Repository

```bash
git clone https://github.com/dewamardana/Web-Scrapper.git
cd Web-Scrapper
```
2. Create and Activate Virtual Environment (optional but recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```
3. Install Dependencies
```bash
pip install -r requirements.txt
```
4. Run the Scraper
```bash
python main.py
```
Then input:

The search keyword (e.g., mental, diabetes, etc.)

The number of articles you want to scrape, or type max for all available

📁 Output
Scraped articles are saved automatically in:
```bash
Data/
├── halodoc.com/
│     └── mental.json
└── alodokter.com/
      └── mental.json
```
Example Output Format (JSON):
```bash
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
```
✅ Requirements
Refer to requirements.txt, but generally you need:

🐍 Python ≥ 3.8

🌐 Google Chrome installed

🔧 ChromeDriver version that matches your Chrome browser

Python Packages:
requests

beautifulsoup4

selenium

💡 Tips
You can simplify ChromeDriver setup using webdriver-manager.

Debug HTML files like debug_alodokter_selenium_pageX.html are saved automatically to assist if scraping fails.

⚠️ Disclaimer
This project is for educational and research purposes only.
All article content is owned by Halodoc and Alodokter.
🛑 Do not use for commercial purposes without permission from the original sources.
