import requests
from bs4 import BeautifulSoup
import json
import time
import math
import os
from urllib.parse import quote

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

session = requests.Session()
session.headers.update(HEADERS)


# ===============================
# SAFE REQUEST (RETRY)
# ===============================
def safe_request(url, retries=3):

    for i in range(retries):
        try:
            res = session.get(url, timeout=20)

            if res.status_code == 200:
                return res

            print(f"⚠️ HTTP {res.status_code} : {url}")

        except Exception as e:
            print(f"⚠️ Request error ({i+1}/{retries}) : {e}")

        time.sleep(2)

    return None


# ===============================
# SCRAPE DETAIL ARTIKEL
# ===============================
def scrape_article(url):

    if "?page=" not in url and "#page" not in url:
        if "?" in url:
            url_all = url + "&page=all"
        else:
            url_all = url + "?page=all"
    else:
        url_all = url

    res = safe_request(url_all)

    if not res:
        raise Exception("Request gagal")

    soup = BeautifulSoup(res.text, "html.parser")

    result = {
        "url": url,
        "sumber_berita": "Kompas.com",
        "judul": "",
        "tanggal_publikasi": "",
        "nama_editor": "",
        "konten_berita": "",
        "tag_berita": "",
    }

    # ======================
    # JUDUL
    # ======================
    title = soup.find("h1", class_="read__title")

    if not title:
        title = soup.find("h1")

    if title:
        result["judul"] = title.get_text(strip=True)

    # ======================
    # TANGGAL
    # ======================
    time_div = soup.find("div", class_="read__time")

    if time_div:
        text = time_div.get_text(" ", strip=True)

        if "," in text:
            try:
                parts = text.split(",")

                if len(parts) >= 2:
                    result["tanggal_publikasi"] = parts[1].replace("WIB", "").strip()
            except:
                pass

    # ======================
    # PENULIS (VERSI BARU)
    # ======================
    editor = soup.select_one("div.clearfix p strong")

    if editor and "Oleh" in editor.text:
        result["nama_editor"] = (
            editor.get_text(strip=True).replace("Oleh:", "").replace("Oleh", "").strip()
        )

    # ======================
    # PENULIS (VERSI LAMA)
    # ======================
    if not result["nama_editor"]:

        old_editor = soup.select_one(".credit-title-nameEditor")

        if old_editor:
            result["nama_editor"] = old_editor.get_text(strip=True)

    # ======================
    # PENULIS (VERSI READ CREDIT)
    # ======================
    if not result["nama_editor"]:

        credit_editor = soup.select_one("#editor a")

        if credit_editor:
            result["nama_editor"] = credit_editor.get_text(strip=True)

    # ======================
    # KONTEN ARTIKEL
    # ======================
    content_container = (
        soup.select_one("#articleContent")
        or soup.select_one(".read__content")
        or soup.select_one("div.clearfix")
    )

    content_parts = []
    seen_text = set()

    if content_container:

        # hapus elemen non artikel
        for tag in content_container.select(
            "script, style, iframe, .ads-on-body, .kompasidRec, "
            ".ads-partner-wrap, .liftdown_v2_tanda, .inject-baca-juga"
        ):
            tag.decompose()

        elements = content_container.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote"]
        )

        for element in elements:

            # ===== HEADING =====
            if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:

                text = element.get_text(" ", strip=True)

                if text and text not in seen_text:
                    content_parts.append(f"\n## {text}\n")
                    seen_text.add(text)

            # ===== PARAGRAPH =====
            elif element.name == "p":

                text = element.get_text(" ", strip=True)

                if not text:
                    continue

                # skip teks tidak relevan
                if text.startswith("Oleh"):
                    continue

                if "Baca juga" in text:
                    continue

                if "KOMPAS.com berkomitmen" in text:
                    continue

                if text not in seen_text:
                    content_parts.append(text)
                    seen_text.add(text)

            # ===== LIST =====
            elif element.name in ["ul", "ol"]:

                for li in element.find_all("li"):

                    li_text = li.get_text(" ", strip=True)

                    if li_text and li_text not in seen_text:
                        content_parts.append(f"- {li_text}")
                        seen_text.add(li_text)

            # ===== QUOTE =====
            elif element.name == "blockquote":

                text = element.get_text(" ", strip=True)

                if text and text not in seen_text:
                    content_parts.append(f"> {text}")
                    seen_text.add(text)

    result["konten_berita"] = "\n".join(content_parts)

    # ======================
    # TAG
    # ======================
    tags = set()

    tag_links = soup.select("div.read__tagging a")

    for tag in tag_links:

        txt = tag.get_text(strip=True)

        if txt:
            tags.add(txt)

    result["tag_berita"] = ", ".join(tags)

    return result


# ===============================
# SAVE JSON AMAN
# ===============================
def safe_save_json(data, output_file):

    temp_file = output_file + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    os.replace(temp_file, output_file)


# ===============================
# SCRAPE SEMUA ARTIKEL
# ===============================
def get_all_article_links(
    query="kesehatan mental", debug=True, output_file="kesehatan-mental.json"
):

    encoded_query = quote(query)

    page = 1
    prev_page_links = set()
    total_pages = None
    scraped_urls = set()

    if os.path.exists(output_file):

        with open(output_file, "r", encoding="utf-8") as f:

            try:
                existing_data = json.load(f)

                for item in existing_data:
                    scraped_urls.add(item["url"])

            except:
                existing_data = []

    else:
        existing_data = []

    print("📂 Mulai scraping...\n")

    while True:

        url = f"https://search.kompas.com/search?q={encoded_query}&site_id=all&last_date=all&type=article&page={page}"

        print(f"\n🔎 Halaman {page}")
        print(f"🌐 {url}")

        res = safe_request(url)

        if not res:
            print("❌ Halaman gagal diakses")
            break

        soup = BeautifulSoup(res.text, "html.parser")

        # ======================
        # TOTAL ARTIKEL
        # ======================
        if total_pages is None:

            count_tag = soup.find("span", id="headArticle-count")

            if count_tag:

                try:
                    total_results = int(count_tag.text.strip())
                    total_pages = math.ceil(total_results / 20)

                    print(
                        f"📊 Total hasil: {total_results} artikel ≈ {total_pages} halaman"
                    )

                except:
                    total_pages = 500
            else:
                total_pages = 500

        # ======================
        # LIST ARTIKEL
        # ======================
        article_list = soup.find("div", class_="articleList")

        items = (
            article_list.find_all("div", class_="articleItem") if article_list else []
        )

        print(f"🧩 Artikel ditemukan: {len(items)}")

        if not items:
            break

        current_page_links = set()

        for item in items:

            a_tag = item.find("a")

            if a_tag and a_tag.get("href"):

                href = a_tag["href"]

                if "tv.kompas.com" not in href:
                    current_page_links.add(href)

        if current_page_links == prev_page_links:
            print("⚠️ Halaman duplikat terdeteksi")
            break

        prev_page_links = current_page_links

        page_data = []

        for i, link in enumerate(current_page_links, start=1):

            if link in scraped_urls:
                print(f"⏭️ Skip (sudah ada) : {link}")
                continue

            print(f"📰 [{page}:{i}] Scraping")

            try:

                article = scrape_article(link)

                page_data.append(article)
                scraped_urls.add(link)

                time.sleep(1)

            except Exception as e:
                print(f"❌ Gagal scrape: {e}")

        if page_data:

            existing_data.extend(page_data)

            safe_save_json(existing_data, output_file)

            print(f"💾 Disimpan {len(page_data)} artikel | Total {len(existing_data)}")

        if total_pages and page >= total_pages:
            print("🏁 Halaman terakhir tercapai")
            break

        page += 1
        time.sleep(2)

    print(f"\n🎯 Total artikel: {len(existing_data)}")

    return existing_data


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":

    query = input("🔍 Kata kunci: ") or "kesehatan mental"

    get_all_article_links(query=query)
