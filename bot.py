import tweepy
import requests
from PIL import Image, ImageDraw, ImageFont
import time
import os

# Chei API (NU le împărtăși nimănui!)
CMC_API_KEY = "b4653eca44924477848ab6cfe76dc2fc"

CONSUMER_KEY = "Yejq1x8ag9mcpWnoAatLc9kWG"
CONSUMER_SECRET = "5TLo1SD9FOnNTEAepPabAIpkGomde001yzjIVhblRtbvBKdhcO"
ACCESS_TOKEN = "1401292538452062208-OPF5iVNIUrln3seUvpShLklNQJLUql"
ACCESS_TOKEN_SECRET = "gaPv1FEJ4fG1uPDhd9OjJM8ZqiphqViXqGEmhGQCQBZrv"

# Autentificare X/Twitter
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api_v1 = tweepy.API(auth)  # pentru upload imagine

client_v2 = tweepy.Client(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Configurări modificabile
# Aici modifici intervalul de verificare in minute
CHECK_INTERVAL_MINUTES = 10

# Aici modifici range-ul pretului (cât să schimbe prețul ca să posteze)
PRICE_CHANGE_THRESHOLD = 10

# Fișiere
TEMPLATE_IMAGE = "template.png"
FONT_FILE = "font.ttf"
OUTPUT_IMAGE = "updated.png"
LAST_PRICE_FILE = "last_price.txt"

# Setări imagine (doar prețul)
# Aici modifici marimea fontului pentru pret (mai mare = umple mai bine chenarul)
PRICE_FONT_SIZE = 200

# Aici modifici centrul vertical al chenarului rosu (mai mare = mai jos)
BOX_CENTER_Y = 245

# Aici modifici culoarea pretului (RGB, alb = (255,255,255))
PRICE_COLOR = (255, 255, 255)

# Funcție preluare preț BNB
def get_bnb_price():
    url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
    parameters = {"symbol": "BNB"}
    headers = {"Accepts": "application/json", "X-CMC_PRO_API_KEY": CMC_API_KEY}
    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()
    price = data["data"]["BNB"][0]["quote"]["USD"]["price"]
    return int(round(price))

# Funcție generare imagine (prețul centrat automat)
def generate_image(price):
    img = Image.open(TEMPLATE_IMAGE)
    draw = ImageDraw.Draw(img)
    price_font = ImageFont.truetype(FONT_FILE, PRICE_FONT_SIZE)
    
    text = f"${price}"
    bbox = draw.textbbox((0, 0), text, font=price_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Centrare orizontală + verticală în chenar
    x = (img.width - text_width) // 2
    y = BOX_CENTER_Y - text_height // 2
    
    draw.text((x, y), text, font=price_font, fill=PRICE_COLOR)
    img.save(OUTPUT_IMAGE)

# Funcție postare pe X
def post_update(price, direction):
    bullet = "🟢" if direction == "up" else "🔴"
    post_text = f"{bullet} #BNB Price: ${price}"
    
    generate_image(price)
    media = api_v1.media_upload(OUTPUT_IMAGE)
    client_v2.create_tweet(text=post_text, media_ids=[media.media_id])
    print("Postare success")

# Încarcă ultimul preț
if os.path.exists(LAST_PRICE_FILE):
    with open(LAST_PRICE_FILE, "r") as f:
        last_price = int(f.read().strip())
else:
    last_price = None

# Preia prețul curent la pornire
current_price = get_bnb_price()

if last_price is None:
    last_price = current_price
    with open(LAST_PRICE_FILE, "w") as f:
        f.write(str(current_price))

print(f"Bot a pornit de la pretul de {last_price}.")

while True:
    try:
        current_price = get_bnb_price()
        
        diff = current_price - last_price
        if abs(diff) >= PRICE_CHANGE_THRESHOLD:
            direction = "up" if diff > 0 else "down"
            post_update(current_price, direction)
            
            last_price = current_price
            with open(LAST_PRICE_FILE, "w") as f:
                f.write(str(current_price))
        
        time.sleep(CHECK_INTERVAL_MINUTES * 60)
    
    except Exception as e:
        print("Eroare:", e)
        time.sleep(60)  # reîncearcă după 1 minut
