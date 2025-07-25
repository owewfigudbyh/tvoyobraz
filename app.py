import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__, static_folder='.')
CORS(app)

# Настройка подключения к MongoDB Atlas
MONGO_URI = "mongodb+srv://aaa17070:komronbek1304@cluster0.ljm0p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['mydb']  # Имя базы данных (можно поменять)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'heic'}

@app.route('/api/list')
def api_list():
    flats = list(db.flats.find().sort("id", -1))
    for flat in flats:
        flat['_id'] = str(flat['_id'])
        flat['images'] = flat.get('images') or []
        flat['utilities'] = flat.get('utilities') or []
    return jsonify(flats)

@app.route('/api/add', methods=['POST'])
def api_add():
    data = request.json
    data['images'] = data.get('images', [])
    data['utilities'] = data.get('utilities', [])
    # Можно добавить автоинкремент для id, если нужно
    result = db.flats.insert_one(data)
    return jsonify({'ok': True, 'inserted_id': str(result.inserted_id)})

@app.route('/api/update', methods=['POST'])
def api_update():
    data = request.json
    card_id = data.get('id')
    if not card_id:
        return jsonify({'error': 'Нет id'}), 400
    data['images'] = data.get('images', [])
    data['utilities'] = data.get('utilities', [])
    result = db.flats.update_one({"id": card_id}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"error": "Объект не найден"}), 404
    return jsonify({'ok': True})

@app.route('/api/delete', methods=['POST'])
def api_delete():
    data = request.json
    card_id = data.get('id')
    if not card_id:
        return jsonify({'error': 'Нет id'}), 400
    result = db.flats.delete_one({"id": card_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Объект не найден"}), 404
    return jsonify({'ok': True})

@app.route('/api/upload', methods=['POST'])
def api_upload():
    files = request.files.getlist('images')
    uploaded = []
    upload_folder = 'uploads'
    os.makedirs(upload_folder, exist_ok=True)
    for file in files:
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            public_url = f"/uploads/{filename}"
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

# Статические файлы из uploads
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
