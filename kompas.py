import requests
from bs4 import BeautifulSoup
import json
import time
import math
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


# --- Fungsi untuk scraping detail artikel ---
def scrape_article(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    result = {
        "url": url,
        "sumber_berita": "",
        "jenis_konten": "",
        "judul": "",
        "tanggal_publikasi": "",
        "jam_publikasi": "",
        "nama_editor": "",
        "jabatan_editor": "",
        "konten_berita": "",
        "tag_berita": "",
    }

    # Breadcrumb
    breadcrumb = soup.find("ul", class_="breadcrumb__wrap")
    if breadcrumb:
        items = breadcrumb.find_all("li", class_="breadcrumb__item")
        if len(items) >= 2:
            result["sumber_berita"] = items[0].get_text(strip=True)
            result["jenis_konten"] = items[1].get_text(strip=True)

    # Judul
    title_tag = soup.find("h1", class_="read__title")
    if title_tag:
        result["judul"] = title_tag.get_text(strip=True)

    # Header (waktu & editor)
    header = soup.find("div", class_="read__header")
    if header:
        time_div = header.find("div", class_="read__time")
        if time_div:
            text = time_div.get_text(strip=True)
            if "-" in text:
                time_text = text.split("-")[-1].strip()
                if "," in time_text:
                    tgl, jam = time_text.split(",")
                    result["tanggal_publikasi"] = tgl.strip()
                    result["jam_publikasi"] = jam.strip()

        credit = header.find("div", class_="credit")
        if credit:
            name_div = credit.find("div", class_="credit-title-nameEditor")
            if name_div:
                result["nama_editor"] = name_div.get_text(strip=True)
            job = credit.find("p")
            if job:
                result["jabatan_editor"] = job.get_text(strip=True)

    # Konten
    content = soup.find("div", class_="read__content")
    if content:
        clear = content.find("div", class_="clearfix")
        if clear:
            blocks = clear.find_all(["p", "h2"])
            paragraphs = [blk.get_text(strip=True) for blk in blocks]
            result["konten_berita"] = "\n".join(paragraphs)

    # Tags
    tags = []
    tag_containers = [
        soup.find("div", class_="read__tagging mt1 clearfix"),
        soup.find("div", class_="tag tag--article clearfix"),
        soup.find("div", class_="tag_article_teaser"),
        soup.find("ul", class_="tag_article_wrap"),
    ]
    for container in tag_containers:
        if container:
            for tag in container.find_all("a"):
                tag_text = tag.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

    result["tag_berita"] = ", ".join(tags)
    return result


# --- Fungsi untuk mengambil semua artikel per halaman dan langsung disimpan ---
def get_all_article_links(
    query="kesehatan mental", debug=True, output_file="kesehatan-mental.json"
):
    all_links = []
    page = 1
    prev_page_links = set()
    total_pages = None

    # Jika file JSON sudah ada → lanjut append
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    print(f"📂 [INFO] Memulai scraping dari halaman 1...")
    print(f"📁 File output: {output_file}\n")

    while True:
        print(f"\n🔄 [DEBUG] Mengambil halaman ke-{page}...")
        url = f"https://search.kompas.com/search?q={query.replace(' ', '+')}&site_id=all&last_date=all&type=article&page={page}"
        print(f"🌐 [DEBUG] URL: {url}")

        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
        except Exception as e:
            print(f"⚠️ [ERROR] Gagal mengakses halaman {page}: {e}")
            page += 1
            continue

        print(f"📶 [DEBUG] Status kode: {res.status_code}")
        if res.status_code != 200:
            print(f"⚠️ Halaman {page} gagal dimuat (status {res.status_code})")
            break

        soup = BeautifulSoup(res.text, "html.parser")

        # ✅ Ambil total artikel (hanya halaman 1)
        if total_pages is None:
            count_tag = soup.find("span", id="headArticle-count")
            if count_tag:
                try:
                    total_results = int(count_tag.text.strip())
                    total_pages = math.ceil(total_results / 20)
                    print(
                        f"📊 [DEBUG] Total hasil pencarian: {total_results} artikel ≈ {total_pages} halaman."
                    )
                except ValueError:
                    total_pages = 499
            else:
                total_pages = 499

        # Ambil daftar artikel di halaman ini
        article_list = soup.find("div", class_="articleList")
        items = (
            article_list.find_all("div", class_="articleItem") if article_list else []
        )
        print(f"🧩 [DEBUG] Jumlah artikel di halaman {page}: {len(items)}")

        if not items:
            print(f"❌ Tidak ada artikel di halaman {page}. Stop scraping.")
            break

        # Ambil semua link di halaman ini
        current_page_links = set()
        for item in items:
            a_tag = item.find("a")
            if a_tag and a_tag.get("href"):
                href = a_tag["href"]
                if "tv.kompas.com" not in href:
                    current_page_links.add(href)

        # 🚨 Deteksi halaman duplikat
        if current_page_links == prev_page_links:
            print("⚠️ [DEBUG] Halaman ini sama dengan sebelumnya. Stop.")
            break
        prev_page_links = current_page_links

        # Scrape tiap artikel di halaman ini
        page_data = []
        for i, link in enumerate(current_page_links, start=1):
            print(f"📰 [{page}:{i}] Scraping artikel: {link}")
            try:
                article = scrape_article(link)
                page_data.append(article)
                time.sleep(1)
            except Exception as e:
                print(f"❌ Gagal scraping artikel: {e}")

        # Simpan hasil halaman ke file JSON (append)
        if page_data:
            existing_data.extend(page_data)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            print(
                f"💾 [SAVED] {len(page_data)} artikel disimpan dari halaman {page}. Total {len(existing_data)} artikel.\n"
            )

        # Stop jika sudah mencapai halaman terakhir
        if total_pages and page >= total_pages:
            print(f"🏁 [DEBUG] Sudah mencapai halaman terakhir ({page}/{total_pages}).")
            break

        page += 1
        time.sleep(2)

    print(f"\n🎯 Total artikel tersimpan: {len(existing_data)}")
    return existing_data


# --- Main eksekusi ---
if __name__ == "__main__":
    query = input("🔍 Masukkan kata kunci pencarian artikel: ") or "kesehatan mental"
    get_all_article_links(query=query)
