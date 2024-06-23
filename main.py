from flask import Flask, request, jsonify, render_template, redirect, url_for
import base64
import re
import os
from datetime import datetime

app = Flask(__name__, static_url_path='/static')

# Ensure the 'static' directory exists
if not os.path.exists('static'):
    os.makedirs('static')

# Endpoint to handle image upload
@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    image_data = data['image']
    # Remove the data:image/png;base64, part
    image_data = re.sub('^data:image/.+;base64,', '', image_data)
    # Decode the image data
    image_data = base64.b64decode(image_data)

    # Save the image with a unique filename
    filename = f'static/selfie_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.png'
    with open(filename, 'wb') as f:
        f.write(image_data)

    return jsonify({'message': 'Image uploaded successfully', 'filename': filename})

# Serve the main page
@app.route('/')
def index():
    return render_template('index.html')

# Serve the admin page
@app.route('/admin')
def admin():
    image_files = os.listdir('static')
    image_files = [f'static/{file}' for file in image_files if file.endswith('.png')]
    return render_template('admin.html', images=image_files)

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
