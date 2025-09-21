import time
import os
import json
import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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

    # Load data lama
    existing_data = load_data("halodoc.com", keyword)
    seen = {item["link"] for item in existing_data}
    data = existing_data[:]
    collected = len(data)
    print(f"📂 Data lama dimuat: {collected} artikel, lanjut scraping...")

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
                print("⚠ Gagal, mencoba ulang...")
                time.sleep(2)
                detail = get_halodoc_article_detail(link)

            if detail:
                data.append(detail)
                collected += 1
                print(f"✅ Berhasil ({collected}/{max_articles})")
            else:
                detail = get_detail_with_retry(get_halodoc_article_detail, link)
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
    print(f"🗂 Halodoc: {len(data)} artikel disimpan.")
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

    # 🔹 Load data lama kalau ada
    existing_data = load_data("alodokter.com", keyword)
    results = {item["link"] for item in existing_data}  # link yang sudah ada
    data = existing_data[:]
    collected = len(data)
    print(f"📂 Alodokter: Data lama {collected} artikel, lanjut scraping...")
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
                print("⚠ Tidak menemukan elemen <card-post-index>")
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
                            print("⚠ Gagal, mencoba ulang...")
                            time.sleep(2)
                            detail = get_alodokter_article_detail(full_url)

                        if detail:
                            data.append(detail)
                            collected += 1
                            print(f"✅ Berhasil ({collected}/{max_articles})")
                        else:
                            detail = get_detail_with_retry(
                                get_halodoc_article_detail, full_url
                            )
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
    print(f"🗂 Alodokter: {len(data)} artikel disimpan.")
    return data


# ============== HALOSEHAT ==============


def parse_author_info(info_text):
    """
    Parsing teks info peninjau/penulis HelloSehat menjadi (reviewer, author, tanggal)
    """
    reviewer = ""

    if not info_text:
        return reviewer

    # Cari reviewer (setelah 'Ditinjau oleh' sampai simbol "·")
    reviewer_match = re.search(r"Ditinjau oleh\s+(.*?)\s+·", info_text)
    if reviewer_match:
        reviewer = reviewer_match.group(1).strip()

    return reviewer


def get_hellosehat_article_detail(url, driver=None):
    """
    Ambil detail artikel HelloSehat: judul, peninjau, tanggal, isi, tag
    """
    try:
        html = None

        # --- coba pakai requests jika kontennya sudah lengkap ---
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.ok and "Reviewer Name" in r.text:
                html = r.text
        except Exception:
            html = None

        # --- fallback: Selenium (untuk elemen yang dirender JS) ---
        if not html and driver:
            driver.get(url)
            try:
                # tunggu anchor reviewer muncul
                WebDriverWait(driver, 12).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'a[data-event-category="Reviewer Name"]')
                    )
                )
            except TimeoutException:
                # minimal tunggu heading jika reviewer tidak ketemu
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                )
            html = driver.page_source

        if not html:
            raise ValueError("Halaman tidak memuat data yang dibutuhkan")

        soup = BeautifulSoup(html, "html.parser")

        # ===== Judul =====
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Info penulis & peninjau
        reviewer = ""
        info_p = soup.select_one("p.mantine-Text-root.mantine-yogv28")
        if info_p:
            text_info = info_p.get_text(" ", strip=True)
            reviewer = parse_author_info(text_info)

        # ===== Tanggal =====
        date = ""
        info_p = soup.find(
            "p", class_="mantine-Text-root mantine-Text-root mantine-yogv28"
        )
        if info_p:
            txt = info_p.get_text(" ", strip=True)
            if "Diperbarui" in txt:
                date = txt.split("Diperbarui")[-1].strip()

        # ===== Isi artikel =====
        content_parts = []
        body = soup.select_one("div.css-jwma8r.eq7z8yn3")
        if body:
            for p in body.select("p"):
                t = p.get_text(" ", strip=True)
                if t and "Baca juga" not in t:
                    content_parts.append(t)

        if not content_parts:
            for p in soup.select("div.body-content.article-content-wrapper p"):
                t = p.get_text(" ", strip=True)
                if t and "Baca juga" not in t:
                    content_parts.append(t)

        content = "\n".join(content_parts)

        # ===== Tags =====
        tags = [
            a.get_text(strip=True)
            for a in soup.select("div.breadcrumbs-top a")
            if a.get_text(strip=True)
        ]

        return {
            "judul_artikel": title,
            "penulis_peninjau": reviewer,
            "tanggal_publish": date,
            "isi_artikel": content,
            "tag": tags,
            "link": url,
            "sumber_data": "hellosehat.com",
        }

    except Exception as e:
        print(f"Gagal HelloSehat ({url}): {e}")
        return None


BASE_URL = (
    "https://hellosehat.com/search/?s={keyword}&tab=articles&page={page}&per_page=10"
)


def search_hellosehat(keyword, max_articles=20):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    # Load data lama
    existing_data = load_data("hellosehat.com", keyword)
    seen = {item["link"] for item in existing_data}
    data = existing_data[:]
    collected = len(data)
    print(f"📂 Data lama dimuat: {collected} artikel, lanjut scraping...")
    page = 1

    try:
        while collected < max_articles:
            url = BASE_URL.format(keyword=keyword, page=page)
            print(f"🌐 Halaman {page}: {url}")
            driver.get(url)

            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'a[data-event-category="Search Page"]')
                    )
                )
            except TimeoutException:
                print("⚠ Tidak menemukan artikel lagi, berhenti.")
                break

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Kumpulkan link artikel
            links = []
            for a in soup.select(
                'a[data-event-category="Search Page"][data-event-action="Articles - Click Article"]'
            ):
                href = a.get("href")
                if not href:
                    continue

                if href.startswith("/"):
                    href_full = "https://hellosehat.com" + href
                else:
                    href_full = href

                if href_full not in seen:
                    seen.add(href_full)
                    links.append(href_full)

            if not links:
                print("⛔ Tidak ada link baru di halaman ini.")
                break

            # Ambil detail tiap artikel
            for link in links:
                if collected >= max_articles:
                    break

                print(f"🔗 Mengambil: {link}")
                detail = get_hellosehat_article_detail(link, driver=driver)

                if not detail:
                    print("⚠ Gagal, mencoba ulang...")
                    time.sleep(2)
                    detail = get_hellosehat_article_detail(link, driver=driver)

                if detail:
                    data.append(detail)
                    collected += 1
                    print(f"✅ Berhasil ({collected}/{max_articles})")
                else:
                    detail = get_detail_with_retry(get_hellosehat_article_detail, link)
                    if detail:
                        data.append(detail)
                        collected += 1
                        print(f"✅ Berhasil ({collected}/{max_articles})")
                    else:
                        print(f"❌ Gagal mengambil: {link}")

                time.sleep(1)

            page += 1
            time.sleep(2)

    finally:
        driver.quit()

    save_data("hellosehat.com", keyword, data)
    print(f"🗂 HelloSehat: {len(data)} artikel disimpan.")
    return data


# ============== SAVE FUNCTION ==============


# ============== COMMON HELPERS ==============


def load_data(source, keyword):
    folder = os.path.join("Data", source)
    filepath = os.path.join(folder, f"{keyword}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_data(source, keyword, data):
    folder = os.path.join("Data", source)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{keyword}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_detail_with_retry(getter_func, url, max_retries=10, driver=None):
    for attempt in range(1, max_retries + 1):
        try:
            detail = getter_func(url) if not driver else getter_func(url, driver=driver)
            if detail:
                print(f"🔗 Berhasil Mengambil URL : {url}")
                return detail
        except Exception as e:
            print(f"⚠ Error ({attempt}/{max_retries}) {url}: {e}")
        time.sleep(2)
    print(f"❌ Gagal total mengambil {url}")
    return None


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
    search_hellosehat(keyword, max_articles=max_artikel)


if __name__ == "__main__":
    keyword = input("🔍 Masukkan kata kunci pencarian artikel: ").strip()
    main(keyword)
