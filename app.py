from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
import math

app = Flask(__name__)
app.secret_key = 'taxi_secret_key_2024'

# Database initialization
def init_db():
    conn = sqlite3.connect('taxi.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            user_type TEXT NOT NULL CHECK (user_type IN ('client', 'driver')),
            whatsapp TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Taxi listings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS taxi_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            description TEXT,
            car_model TEXT,
            price_per_km REAL,
            is_active BOOLEAN DEFAULT 1,
            views_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES users (id)
        )
    ''')
    
    # Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (listing_id) REFERENCES taxi_listings (id),
            FOREIGN KEY (client_id) REFERENCES users (id)
        )
    ''')
    
    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (listing_id) REFERENCES taxi_listings (id),
            FOREIGN KEY (client_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('taxi.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')
        whatsapp = data.get('whatsapp', '')
        
        if not all([username, email, password, user_type]):
            return jsonify({'success': False, 'message': 'Все поля обязательны'})
        
        if user_type not in ['client', 'driver']:
            return jsonify({'success': False, 'message': 'Неверный тип пользователя'})
        
        conn = get_db_connection()
        
        # Check if user already exists
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()
        
        if existing_user:
            conn.close()
            return jsonify({'success': False, 'message': 'Пользователь уже существует'})
        
        # Create new user
        password_hash = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (username, email, password_hash, user_type, whatsapp) VALUES (?, ?, ?, ?, ?)',
            (username, email, password_hash, user_type, whatsapp)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Регистрация успешна'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'success': False, 'message': 'Все поля обязательны'})
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            return jsonify({'success': True, 'user_type': user['user_type']})
        else:
            return jsonify({'success': False, 'message': 'Неверные данные'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['user_type'] == 'driver':
        return render_template('driver_dashboard.html')
    else:
        return render_template('client_dashboard.html')

@app.route('/api/create_listing', methods=['POST'])
def create_listing():
    if 'user_id' not in session or session['user_type'] != 'driver':
        return jsonify({'success': False, 'message': 'Доступ запрещен'})
    
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    description = data.get('description', '')
    car_model = data.get('car_model', '')
    price_per_km = data.get('price_per_km', 0)
    
    if not all([latitude, longitude]):
        return jsonify({'success': False, 'message': 'Координаты обязательны'})
    
    conn = get_db_connection()
    
    # Deactivate previous listings
    conn.execute(
        'UPDATE taxi_listings SET is_active = 0 WHERE driver_id = ?',
        (session['user_id'],)
    )
    
    # Create new listing
    conn.execute(
        'INSERT INTO taxi_listings (driver_id, latitude, longitude, description, car_model, price_per_km) VALUES (?, ?, ?, ?, ?, ?)',
        (session['user_id'], latitude, longitude, description, car_model, price_per_km)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Объявление создано'})

@app.route('/api/end_listing', methods=['POST'])
def end_listing():
    if 'user_id' not in session or session['user_type'] != 'driver':
        return jsonify({'success': False, 'message': 'Доступ запрещен'})
    
    conn = get_db_connection()
    conn.execute(
        'UPDATE taxi_listings SET is_active = 0 WHERE driver_id = ? AND is_active = 1',
        (session['user_id'],)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Объявление завершено'})

@app.route('/api/get_nearby_taxis')
def get_nearby_taxis():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', 10, type=float)  # km
    
    if not all([lat, lon]):
        return jsonify({'success': False, 'message': 'Координаты обязательны'})
    
    conn = get_db_connection()
    listings = conn.execute('''
        SELECT tl.*, u.username, u.whatsapp 
        FROM taxi_listings tl 
        JOIN users u ON tl.driver_id = u.id 
        WHERE tl.is_active = 1
    ''').fetchall()
    conn.close()
    
    nearby_taxis = []
    for listing in listings:
        distance = calculate_distance(lat, lon, listing['latitude'], listing['longitude'])
        if distance <= radius:
            nearby_taxis.append({
                'id': listing['id'],
                'driver_name': listing['username'],
                'latitude': listing['latitude'],
                'longitude': listing['longitude'],
                'description': listing['description'],
                'car_model': listing['car_model'],
                'price_per_km': listing['price_per_km'],
                'distance': round(distance, 2),
                'views_count': listing['views_count'],
                'whatsapp': listing['whatsapp']
            })
    
    # Sort by distance
    nearby_taxis.sort(key=lambda x: x['distance'])
    
    return jsonify({'success': True, 'taxis': nearby_taxis})

@app.route('/api/view_listing/<int:listing_id>')
def view_listing(listing_id):
    conn = get_db_connection()
    
    # Increment view count
    conn.execute(
        'UPDATE taxi_listings SET views_count = views_count + 1 WHERE id = ?',
        (listing_id,)
    )
    
    # Get listing details
    listing = conn.execute('''
        SELECT tl.*, u.username, u.whatsapp 
        FROM taxi_listings tl 
        JOIN users u ON tl.driver_id = u.id 
        WHERE tl.id = ?
    ''', (listing_id,)).fetchone()
    
    if not listing:
        conn.close()
        return jsonify({'success': False, 'message': 'Объявление не найдено'})
    
    # Get reviews
    reviews = conn.execute('''
        SELECT r.*, u.username 
        FROM reviews r 
        JOIN users u ON r.client_id = u.id 
        WHERE r.listing_id = ? 
        ORDER BY r.created_at DESC
    ''', (listing_id,)).fetchall()
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'listing': {
            'id': listing['id'],
            'driver_name': listing['username'],
            'description': listing['description'],
            'car_model': listing['car_model'],
            'price_per_km': listing['price_per_km'],
            'whatsapp': listing['whatsapp'],
            'views_count': listing['views_count']
        },
        'reviews': [dict(review) for review in reviews]
    })

@app.route('/api/book_taxi', methods=['POST'])
def book_taxi():
    if 'user_id' not in session or session['user_type'] != 'client':
        return jsonify({'success': False, 'message': 'Доступ запрещен'})
    
    data = request.get_json()
    listing_id = data.get('listing_id')
    
    if not listing_id:
        return jsonify({'success': False, 'message': 'ID объявления обязателен'})
    
    conn = get_db_connection()
    
    # Check if listing exists and is active
    listing = conn.execute(
        'SELECT * FROM taxi_listings WHERE id = ? AND is_active = 1',
        (listing_id,)
    ).fetchone()
    
    if not listing:
        conn.close()
        return jsonify({'success': False, 'message': 'Объявление не найдено или неактивно'})
    
    # Create booking
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO bookings (listing_id, client_id) VALUES (?, ?)',
        (listing_id, session['user_id'])
    )
    
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Такси забронировано',
        'booking_id': booking_id,
        'receipt': {
            'booking_id': booking_id,
            'car_model': listing['car_model'],
            'price_per_km': listing['price_per_km'],
            'description': listing['description']
        }
    })

@app.route('/api/add_review', methods=['POST'])
def add_review():
    if 'user_id' not in session or session['user_type'] != 'client':
        return jsonify({'success': False, 'message': 'Доступ запрещен'})
    
    data = request.get_json()
    listing_id = data.get('listing_id')
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    if not all([listing_id, rating]):
        return jsonify({'success': False, 'message': 'ID объявления и рейтинг обязательны'})
    
    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Неверный формат рейтинга'})
    
    if not (1 <= rating <= 5):
        return jsonify({'success': False, 'message': 'Рейтинг должен быть от 1 до 5'})
    
    conn = get_db_connection()
    
    # Check if user already reviewed this listing
    existing_review = conn.execute(
        'SELECT id FROM reviews WHERE listing_id = ? AND client_id = ?',
        (listing_id, session['user_id'])
    ).fetchone()
    
    if existing_review:
        conn.close()
        return jsonify({'success': False, 'message': 'Вы уже оставили отзыв'})
    
    # Add review
    conn.execute(
        'INSERT INTO reviews (listing_id, client_id, rating, comment) VALUES (?, ?, ?, ?)',
        (listing_id, session['user_id'], rating, comment)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Отзыв добавлен'})

@app.route('/api/driver_stats')
def driver_stats():
    if 'user_id' not in session or session['user_type'] != 'driver':
        return jsonify({'success': False, 'message': 'Доступ запрещен'})
    
    conn = get_db_connection()
    
    # Get current active listing
    active_listing = conn.execute(
        'SELECT * FROM taxi_listings WHERE driver_id = ? AND is_active = 1',
        (session['user_id'],)
    ).fetchone()
    
    # Get total views
    total_views = conn.execute(
        'SELECT SUM(views_count) as total FROM taxi_listings WHERE driver_id = ?',
        (session['user_id'],)
    ).fetchone()
    
    # Get total bookings
    total_bookings = conn.execute('''
        SELECT COUNT(*) as total 
        FROM bookings b 
        JOIN taxi_listings tl ON b.listing_id = tl.id 
        WHERE tl.driver_id = ?
    ''', (session['user_id'],)).fetchone()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'has_active_listing': active_listing is not None,
        'active_listing': dict(active_listing) if active_listing else None,
        'total_views': total_views['total'] or 0,
        'total_bookings': total_bookings['total'] or 0
    })

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=12000, debug=True)