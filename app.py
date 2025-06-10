import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__, static_folder='.')

SUPABASE_URL = "https://zgyiebfsfyccssvdjogi.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpneWllYmZzZnljY3NzdmRqb2dpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1NTMwMjYsImV4cCI6MjA2NTEyOTAyNn0.z5sVR6TAbjkzgwaEdrsy-7F804_aciiQlOSAhmh2obw"
SUPABASE_BUCKET = "images"  # Имя bucket в Supabase Storage
SUPABASE_TABLE = "flats"
SUPABASE_REST = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def upload_to_supabase_storage(file, filename):
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": file.content_type
    }
    resp = requests.post(url, headers=headers, data=file.read())
    if resp.status_code not in (200, 201):
        return None
    # Получить публичный URL
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
    return public_url

@app.route('/api/list')
def api_list():
    r = requests.get(SUPABASE_REST + "?order=id.desc", headers=HEADERS)
    flats = r.json()
    for flat in flats:
        flat['images'] = flat.get('images') or []
        flat['utilities'] = flat.get('utilities') or []
    return jsonify(flats)

@app.route('/api/add', methods=['POST'])
def api_add():
    data = request.json
    data['images'] = data.get('images', [])
    data['utilities'] = data.get('utilities', [])
    r = requests.post(SUPABASE_REST, headers=HEADERS, data=json.dumps(data))
    if r.status_code not in (201, 200):
        return jsonify({"error": r.text}), 400
    return jsonify({'ok': True})

@app.route('/api/update', methods=['POST'])
def api_update():
    data = request.json
    card_id = data.get('id')
    if not card_id:
        return jsonify({'error': 'Нет id'}), 400
    data['images'] = data.get('images', [])
    data['utilities'] = data.get('utilities', [])
    url = SUPABASE_REST + f"?id=eq.{card_id}"
    r = requests.patch(url, headers=HEADERS, data=json.dumps(data))
    if r.status_code not in (204, 200):
        return jsonify({"error": r.text}), 400
    return jsonify({'ok': True})

@app.route('/api/delete', methods=['POST'])
def api_delete():
    data = request.json
    card_id = data.get('id')
    if not card_id:
        return jsonify({'error': 'Нет id'}), 400
    url = SUPABASE_REST + f"?id=eq.{card_id}"
    r = requests.delete(url, headers=HEADERS)
    if r.status_code not in (204, 200):
        return jsonify({"error": r.text}), 400
    return jsonify({'ok': True})

@app.route('/api/upload', methods=['POST'])
def api_upload():
    files = request.files.getlist('images')
    uploaded = []
    for file in files:
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            public_url = upload_to_supabase_storage(file, filename)
            if public_url:
                uploaded.append(public_url)
    if not uploaded:
        return jsonify({'error': 'Ошибка загрузки файлов'}), 400
    return jsonify({'uploaded': uploaded})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(port=5000, debug=True)
