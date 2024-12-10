import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
import os

# Koneksi ke MongoDB
client = MongoClient(os.environ['MONGODB_URI'])
db = client['EPIC_GAMES_FGDB']  # Mengubah nama database
collection = db['sent_entries']

# URL RSS Feed
rss_url = 'https://feed.phenx.de/lootscraper_epic_game.xml'
response = requests.get(rss_url)

# Parsing XML
soup = BeautifulSoup(response.content, 'xml')
entries = soup.find_all('entry')

# Kirim setiap entry yang belum pernah dikirim
for entry in entries:
    title = entry.title.text.replace("Epic Games (Game) - ", "").strip()  # Menghapus "Epic Games (Game) - "
    link = entry.link['href']
    content = entry.content
    image_url = content.find('img')['src']
    
    # Mengambil ID dari entry
    entry_id = entry.id.text  # Mengambil ID dari feed RSS

    # Mengambil tanggal dari konten
    offer_valid_from = content.find_all('li')[0].text.split(": ")[1].split(" - ")[0]
    offer_valid_to = content.find_all('li')[1].text.split(": ")[1].split(" - ")[0]

    # Perubahan: Mengambil tahun dari Offer valid from
    year_from = offer_valid_from.split("-")[0]  # Mendapatkan tahun dari offer_valid_from
    month_from, day_from = offer_valid_from.split("-")[1], offer_valid_from.split("-")[2]
    
    # Perubahan: Mendapatkan bulan dan hari dari offer_valid_to, tetap menggunakan tahun dari offer_valid_from
    month_to, day_to = offer_valid_to.split("-")[1], offer_valid_to.split("-")[2]

    # Perubahan: Membentuk tanggal dengan tahun yang lengkap
    formatted_offer_valid_from = f"{year_from}-{month_from}-{day_from}"  # Format tahun lengkap
    formatted_offer_valid_to = f"{year_from}-{month_to}-{day_to}"  # Menggunakan tahun yang sama
    
    # Format pesan
    message = f"🎮 {title}\n\n📅 Offer valid from: {formatted_offer_valid_from} to {formatted_offer_valid_to}"

    # Cek apakah entri sudah ada di database
    if collection.find_one({"entry_id": entry_id}) is None:  # Menggunakan entry_id sebagai kunci
        # Kirim pesan ke Telegram
        telegram_url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendPhoto"
        payload = {
            "chat_id": os.environ['TELEGRAM_CHAT_ID'],
            "photo": image_url,
            "caption": message,
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🎁 Claim Game", "url": link}
                ]]
            }
        }
        response = requests.post(telegram_url, json=payload)

        # Output status pengiriman
        if response.status_code == 200:
            print(f"✅ Berhasil mengirim pesan: {title}")
        else:
            print(f"❌ Gagal mengirim pesan: {title}. Kode status: {response.status_code}")

        # Simpan entri ke database untuk menghindari duplikasi
        collection.insert_one({"entry_id": entry_id})  # Menyimpan ID entri
    else:
        print(f"🚫 Sudah melewati entri yang sudah dikirim: {title}")
