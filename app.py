import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory, g
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, static_folder='.')

DATABASE = 'flats.db'
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS flats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                images TEXT,
                address TEXT,
                description TEXT,
                area_house TEXT,
                area_land TEXT,
                land_category TEXT,
                status TEXT,
                material TEXT,
                condition TEXT,
                utilities TEXT,
                village TEXT,
                price TEXT
            )
        ''')
        db.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/list')
def api_list():
    db = get_db()
    flats = db.execute('SELECT * FROM flats').fetchall()
    result = []
    for f in flats:
        obj = dict(f)
        # images и utilities храним как строку (json), декодируем обратно в массив
        import json
        obj['images'] = json.loads(obj['images']) if obj['images'] else []
        obj['utilities'] = json.loads(obj['utilities']) if obj['utilities'] else []
        result.append(obj)
    return jsonify(result)

@app.route('/api/add', methods=['POST'])
def api_add():
    db = get_db()
    data = request.json
    import json
    db.execute('''
        INSERT INTO flats (images, address, description, area_house, area_land, land_category, status, material, condition, utilities, village, price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        json.dumps(data.get('images', [])),
        data.get('address'),
        data.get('description'),
        data.get('area_house'),
        data.get('area_land'),
        data.get('land_category'),
        data.get('status'),
        data.get('material'),
        data.get('condition'),
        json.dumps(data.get('utilities', [])),
        data.get('village'),
        data.get('price'),
    ))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/update', methods=['POST'])
def api_update():
    db = get_db()
    data = request.json
    import json
    card_id = data.get('id')
    if card_id is None:
        return jsonify({'error': 'Нет id'}), 400
    db.execute('''
        UPDATE flats SET
            images=?, address=?, description=?, area_house=?, area_land=?, land_category=?,
            status=?, material=?, condition=?, utilities=?, village=?, price=?
        WHERE id=?
    ''', (
        json.dumps(data.get('images', [])),
        data.get('address'),
        data.get('description'),
        data.get('area_house'),
        data.get('area_land'),
        data.get('land_category'),
        data.get('status'),
        data.get('material'),
        data.get('condition'),
        json.dumps(data.get('utilities', [])),
        data.get('village'),
        data.get('price'),
        card_id
    ))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/delete', methods=['POST'])
def api_delete():
    db = get_db()
    data = request.json
    card_id = data.get('id')
    if card_id is None:
        return jsonify({'error': 'Нет id'}), 400
    db.execute('DELETE FROM flats WHERE id=?', (card_id,))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/upload', methods=['POST'])
def api_upload():
    files = request.files.getlist('file')
    urls = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            urls.append(f"/static/images/{unique_filename}")
    if not urls:
        return jsonify({'error': 'Нет валидных файлов'}), 400
    return jsonify({'urls': urls})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    init_db()
    app.run(port=5000, debug=True)
