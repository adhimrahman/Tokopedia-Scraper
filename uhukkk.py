# Import Library
# Selenium untuk ngontrol browser otomatis (klik, open, scroll)
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup   # BeautifulSoup untuk baca dan ngurai page HTML
import time                     # time untuk ngatur jeda
import csv                      # csv untuk menyimpan output ke format csv

# Setup Chrome Driver ( ngatur entry ke Google Chrome biar bisa dikontrol sm python )
# chromedriver.exe is a tools so Python can communicate with Chrome.
service = Service('D:/(PATH)/chromedriver.exe')
driver = webdriver.Chrome(service=service)

base_url = 'https://www.tokopedia.com/(toko)'    # url toko tokped / link utama yg bakal dibuka

current_page = 1    # nomor halaman awal mulai untuk pagination
productDatas = []   # array kosong untuk nyimpan semua data produk (tolong beri contoh)

while True: # loop untuk ngulangi proses browsing sampai page terakhir
    url = f'{base_url}/page/{current_page}' if current_page > 1 else base_url       # if halaman pertama = base_url else tambah /page/2, /page/3, dst
    print(f'\n=== Memproses Halaman {current_page} ===')
    driver.get(url)
    time.sleep(6)       # tgg 6 detik buat load page

    # SCROLL SAMPAI SEMUA PRODUK MUNCUL
    # tokped tdk langsung load semua produk di awal, dia pakai teknik lazy load (load bertahap).
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")

    # scroll pelan" (naik 1000 px per 1000 px), lalu cek: tinggi halaman berubah atau tidak?
    # if tdk berubah lg, artinya semua produk sudah terlaod, stop scroll.
    while True:
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height

    # SCRAPE PRODUK DI HALAMAN INI
    soup = BeautifulSoup(driver.page_source, 'html.parser')                     # baca seluruh page
    prodCards = soup.find_all('div', {'data-testid': 'master-product-card'})    # cari semua blok produk
    mainWindow = driver.current_window_handle                                   # keep window utama (yg aktif) buat balik setelah buka tab baru

    print(f'Jumlah produk ditemukan: {len(prodCards)}')     # cek jumlah produk pada halaman tersebut

    for idx, card in enumerate(prodCards, start=1):         # untuk tiap produk ambil nama, harga, gambar, link
        try:
            name = card.find('div', {'data-testid': 'linkProductName'}).get_text()
            price = card.find('div', {'data-testid': 'linkProductPrice'}).get_text()
            image = card.find('img', {'data-testid': 'imgProduct'})['src']
            link = card.find('a', class_='pcv3__info-content')['href']

            # BUKA PRODUK DI TAB BARU
            driver.execute_script(f"window.open('{link}', '_blank');")
            time.sleep(3)

            # switch ke tab baru (paling akhir)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(3)

            # KLIK "LIHAT SELENGKAPNYA" JIKA ADA
            try:
                btn_see_more = driver.find_element(By.XPATH, '//button[@data-testid="btnPDPSeeMore"]')
                btn_see_more.click()
                time.sleep(2)
            except NoSuchElementException:
                pass  # kalau tidak ada, lanjut saja

            detailSoup = BeautifulSoup(driver.page_source, 'html.parser')
            tagDesc = detailSoup.find('div', {'data-testid': 'lblPDPDescriptionProduk'})
            desc = tagDesc.get_text() if tagDesc else 'No desc'

            # simpan data
            productDatas.append({
                'name': name,
                'price': price,
                'image': image,
                'desc': desc,
                'link': link
            })
            print(f'[{idx}/{len(prodCards)}] Sukses ambil data: {name}')

            # TUTUP TAB PRODUK
            driver.close()
            driver.switch_to.window(mainWindow)
            time.sleep(2)
        except Exception as e:
            print(f'Gagal ambil data produk: {e}')
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(mainWindow)
            continue

    # CEK APAKAH ADA TOMBOL NEXT
    try:
        next_btn = driver.find_element(By.XPATH, '//a[@data-testid="btnShopProductPageNext"]')
        if next_btn and next_btn.is_enabled():
            current_page += 1
        else:
            print('Tidak ada halaman berikutnya, selesai.')
            break
    except NoSuchElementException:
        print('Tidak ada tombol next, scraping selesai.')
        break

# csv
with open('prods.csv', 'w', newline='', encoding='utf-8') as csvfile:
    field = ['name', 'price', 'image', 'desc', 'link']
    writer = csv.DictWriter(csvfile, fieldnames=field)
    writer.writeheader()
    for product in productDatas:
        writer.writerow(product)

print('\n=== Scraping selesai. Data disimpan di file csv ===')
driver.quit()   # tutup browser