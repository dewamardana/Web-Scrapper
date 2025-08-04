import time
import os
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# ============== HALODOC ==============


def get_halodoc_article_detail(url):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title_tag = soup.find("h1") or soup.select_one(
            "h3.section-header__content-text-title"
        )
        title = title_tag.get_text(strip=True) if title_tag else ""

        author_tag = soup.select_one("div.article-page__reviewer a.hd-base-links")
        author = author_tag.get_text(strip=True) if author_tag else ""

        date = ""
        date_container = soup.select_one("div.article-page__reviewer")
        if date_container:
            for span in date_container.find_all("span"):
                text = span.get_text(strip=True)
                if any(
                    b in text
                    for b in [
                        "Januari",
                        "Februari",
                        "Maret",
                        "April",
                        "Mei",
                        "Juni",
                        "Juli",
                        "Agustus",
                        "September",
                        "Oktober",
                        "November",
                        "Desember",
                    ]
                ):
                    date = text
                    break

        content_tags = soup.select("div[class*=content] p, div.css-16z3ifd p")
        content = "\n".join(p.get_text(strip=True) for p in content_tags)

        tag_labels = soup.select("div.label-container label")
        tags = [t.get_text(strip=True) for t in tag_labels]

        return {
            "judul_artikel": title,
            "penulis_peninjau": author,
            "tanggal_publish": date,
            "isi_artikel": content,
            "tag": tags,
            "link": url,
            "sumber_data": "halodoc.com",
        }

    except Exception as e:
        print(f"Gagal Halodoc ({url}): {e}")
        return None


def search_halodoc(keyword, max_articles=20):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(f"https://www.halodoc.com/artikel/search/{keyword}")
    wait = WebDriverWait(driver, 10)

    data = []
    seen = set()
    collected = 0

    while collected < max_articles:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select("a[href^='/artikel/']")
        new_links = []

        for a in links:
            href = a.get("href")
            full_link = f"https://www.halodoc.com{href}"
            if full_link not in seen:
                seen.add(full_link)
                new_links.append(full_link)

        for link in new_links:
            if collected >= max_articles:
                break

            print(f"🔗 Mengambil: {link}")
            detail = get_halodoc_article_detail(link)

            if not detail:
                print("⚠️ Gagal, mencoba ulang...")
                time.sleep(2)
                detail = get_halodoc_article_detail(link)

            if detail:
                data.append(detail)
                collected += 1
                print(f"✅ Berhasil ({collected}/{max_articles})")
            else:
                print(f"❌ Gagal mengambil: {link}")

            time.sleep(1)

        try:
            load_more = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Selanjutnya')]")
                )
            )
            driver.execute_script("arguments[0].click();", load_more)
            time.sleep(2)
        except:
            print("⛔ Tidak ada tombol 'Selanjutnya' lagi.")
            break

    driver.quit()
    save_data("halodoc.com", keyword, data)
    print(f"🗂️ Halodoc: {len(data)} artikel disimpan.")
    return data


# ============== ALODOKTER ==============


def get_alodokter_article_detail(url):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

        author = ""
        sources_post = soup.find("sources-post")
        if sources_post and sources_post.has_attr("doctor-name"):
            author = sources_post["doctor-name"].strip()

        if not author:
            reviewer = soup.select_one("div.review-doctor")
            if reviewer:
                raw = reviewer.get_text(strip=True)
                if "Ditinjau oleh" in raw:
                    author = raw.split("oleh")[-1].strip()

        date_tag = soup.select_one("div.date-article")
        date = (
            date_tag.get_text(strip=True).replace("Terakhir diperbarui:", "").strip()
            if date_tag
            else ""
        )

        article_content = soup.select_one("div#postContent")
        content = (
            "\n".join(p.get_text(strip=True) for p in article_content.find_all("p"))
            if article_content
            else ""
        )

        tag_labels = soup.select("div.tag-label-container .tag-label")
        tags = [t.get_text(strip=True) for t in tag_labels]

        return {
            "judul_artikel": title,
            "penulis_peninjau": author,
            "tanggal_publish": date,
            "isi_artikel": content,
            "tag": tags,
            "link": url,
            "sumber_data": "alodokter.com",
        }

    except Exception as e:
        print(f"Gagal Alodokter ({url}): {e}")
        return None


def search_alodokter(keyword, max_articles=3):
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    data = []
    results = set()
    collected = 0
    page = 1

    try:
        while collected < max_articles:
            url = f"https://www.alodokter.com/search?s={keyword}&page={page}"
            print(f"🌐 Halaman {page}: {url}")
            driver.get(url)
            time.sleep(3)  # Ganti WebDriverWait dengan sleep sementara

            # Simpan HTML untuk debug
            with open(
                f"debug_alodokter_selenium_page{page}.html", "w", encoding="utf-8"
            ) as f:
                f.write(driver.page_source)

            # Gunakan BeautifulSoup untuk parse elemen <card-post-index>
            soup = BeautifulSoup(driver.page_source, "html.parser")
            cards = soup.find_all("card-post-index")

            if not cards:
                print("⚠️ Tidak menemukan elemen <card-post-index>")
                break

            for card in cards:
                if collected >= max_articles:
                    break

                path = card.get("url-path")
                if path:
                    full_url = f"https://www.alodokter.com{path}"
                    if full_url not in results:
                        results.add(full_url)
                        print(f"🔗 Mengambil: {full_url}")

                        detail = get_alodokter_article_detail(full_url)
                        if not detail:
                            print("⚠️ Gagal, mencoba ulang...")
                            time.sleep(2)
                            detail = get_alodokter_article_detail(full_url)

                        if detail:
                            data.append(detail)
                            collected += 1
                            print(f"✅ Berhasil ({collected}/{max_articles})")
                        else:
                            print(f"❌ Gagal mengambil: {full_url}")

                        time.sleep(1)
            page += 1

    finally:
        driver.quit()

    print(f"\n🔚 Total link unik ditemukan: {len(results)}")
    save_data("alodokter.com", keyword, data)
    print(f"🗂️ Alodokter: {len(data)} artikel disimpan.")
    return data


# ============== SAVE FUNCTION ==============


def save_data(source, keyword, data):
    folder = os.path.join("Data", source)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{keyword}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============== MAIN ==============


def main(keyword):
    try:
        max_artikel = input(
            "🧮 Masukkan jumlah artikel yang ingin dicari (atau 'max' untuk semua): "
        ).strip()
        if max_artikel.lower() == "max":
            max_artikel = 5000  # Atur limit tinggi agar dianggap 'semua'
        else:
            max_artikel = int(max_artikel)
    except ValueError:
        print("❌ Input tidak valid, menggunakan default 20 artikel.")
        max_artikel = 20

    search_halodoc(keyword, max_articles=max_artikel)
    search_alodokter(keyword, max_articles=max_artikel)


if __name__ == "__main__":
    keyword = input("🔍 Masukkan kata kunci pencarian artikel: ").strip()
    main(keyword)
