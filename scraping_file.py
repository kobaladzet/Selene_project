import requests
from bs4 import BeautifulSoup
import sqlite3
import time

# Connect to SQLite database
connection = sqlite3.connect("collections.sqlite")
cursor = connection.cursor()



# Create the collections table

cursor.execute('''DROP TABLE IF EXISTS collections''')
cursor.execute('''
    
    CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY,
        Title VARCHAR(200),
        Artist VARCHAR(200),
        Date VARCHAR(50),
        Dimensions VARCHAR(100),
        Image VARCHAR(200),
        Price INTEGER
    )
''')

connection.commit()


domain = "https://www.daraba.art"
for page in range(1, 15):
    url = f"{domain}/en/artworks?page={page}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch page {page}: {response.status_code}")
        continue

    soup = BeautifulSoup(response.text, 'html.parser')

    items = soup.find_all("div", class_="article-item")
    for item in items:
        time.sleep(4)
        try:
            title = item.find("h4", class_="title").text.strip()
            artist = item.find("h6", class_="author").text.strip()
            price = item.find("span", class_="new-price").text.strip()
            image_tag = item.find("div", class_="image-container")
            image_url = image_tag.find("img")["src"] if image_tag else ""

            # Download and save the image
            image_name = image_url.split("/")[-1]
            image_path = f"static/images/drawings/{image_name}"
            if image_url:
                with open(image_path, "wb") as img_file:
                    img_file.write(requests.get(image_url).content)

            item_url = image_tag.find("a")["href"]
            item_content = requests.get(item_url).text

            item_soup = BeautifulSoup(item_content, "html.parser")
            description = item_soup.find_all("div", class_="product_common_description")
            date = description[0].text.replace("\n", "")
            dimensions = description[2].text.replace("\n", "")

            sql_tuple = (title, artist, price, image_name, date, dimensions)

            cursor.execute('''
            
                INSERT INTO collections (Title, Artist,  Price, Image, Date, Dimensions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', sql_tuple)
            connection.commit()
            print(sql_tuple)

        except Exception as e:
            print(f"Error processing item: {e}")
    time.sleep(10)

# Verify table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Existing tables:", cursor.fetchall())

connection.close()
