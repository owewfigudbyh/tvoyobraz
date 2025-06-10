import os
import json
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')

FLATS_PATH = 'flats.json'
cache = {}

def load_flats():
    if 'flats' not in cache:
        if os.path.exists(FLATS_PATH):
            with open(FLATS_PATH, encoding='utf-8') as f:
                cache['flats'] = json.load(f)
        else:
            cache['flats'] = []
    return cache['flats']

def save_flats(flats):
    # На Vercel это не будет работать для production, но локально можно.
    # Для production лучше подключить внешнюю БД (например, Supabase, Firebase или Google Sheets).
    with open(FLATS_PATH, 'w', encoding='utf-8') as f:
        json.dump(flats, f, ensure_ascii=False, indent=2)
    cache['flats'] = flats

@app.route('/api/list')
def api_list():
    return jsonify(load_flats())

@app.route('/api/add', methods=['POST'])
def api_add():
    flats = load_flats()
    data = request.json
    data['id'] = max([x.get('id', 0) for x in flats] or [0]) + 1
    flats.append(data)
    save_flats(flats)
    return jsonify({'ok': True})

@app.route('/api/delete', methods=['POST'])
def api_delete():
    flats = load_flats()
    data = request.json
    card_id = data.get('id')
    if card_id is None:
        return jsonify({'error': 'Нет id'}), 400
    try:
        card_id = int(card_id)
    except:
        return jsonify({'error': 'Некорректный id'}), 400
    new_flats = [f for f in flats if int(f.get('id')) != card_id]
    if len(flats) == len(new_flats):
        return jsonify({'error': 'Объект не найден'}), 404
    save_flats(new_flats)
    return jsonify({'ok': True})

@app.route('/api/update', methods=['POST'])
def api_update():
    flats = load_flats()
    data = request.json
    card_id = data.get('id')
    if card_id is None:
        return jsonify({'error': 'Нет id'}), 400
    try:
        card_id = int(card_id)
    except:
        return jsonify({'error': 'Некорректный id'}), 400
    updated = False
    for i, flat in enumerate(flats):
        if int(flat.get('id')) == card_id:
            data['id'] = card_id
            flats[i] = data
            updated = True
            break
    if not updated:
        return jsonify({'error': 'Объект не найден'}), 404
    save_flats(flats)
    return jsonify({'ok': True})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')
@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)
