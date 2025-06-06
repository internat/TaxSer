#!/usr/bin/env python3
"""
Скрипт для добавления тестовых данных в базу данных
"""

import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def add_test_data():
    conn = sqlite3.connect('taxi.db')
    cursor = conn.cursor()
    
    # Добавляем тестовых пользователей
    test_users = [
        ('client1', 'client1@test.com', 'password123', 'client', ''),
        ('client2', 'client2@test.com', 'password123', 'client', ''),
        ('driver1', 'driver1@test.com', 'password123', 'driver', '+79161234567'),
        ('driver2', 'driver2@test.com', 'password123', 'driver', '+79167654321'),
        ('driver3', 'driver3@test.com', 'password123', 'driver', '+79169876543'),
    ]
    
    for username, email, password, user_type, whatsapp in test_users:
        password_hash = generate_password_hash(password)
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, user_type, whatsapp) VALUES (?, ?, ?, ?, ?)',
                (username, email, password_hash, user_type, whatsapp)
            )
            print(f"Добавлен пользователь: {username}")
        except sqlite3.IntegrityError:
            print(f"Пользователь {username} уже существует")
    
    # Получаем ID водителей
    driver_ids = cursor.execute(
        'SELECT id FROM users WHERE user_type = "driver"'
    ).fetchall()
    
    # Добавляем тестовые объявления такси (координаты Москвы и окрестностей)
    test_listings = [
        # Центр Москвы
        (55.7558, 37.6176, 'Комфортное такси в центре города', 'Toyota Camry', 30.0),
        (55.7522, 37.6156, 'Быстрая доставка по городу', 'Hyundai Solaris', 25.0),
        (55.7601, 37.6184, 'Премиум класс, кондиционер', 'Mercedes E-Class', 50.0),
        
        # Другие районы Москвы
        (55.7887, 37.6094, 'Эконом класс, чистый салон', 'Lada Vesta', 20.0),
        (55.7342, 37.5977, 'Семейное такси, детские кресла', 'Volkswagen Touran', 35.0),
        (55.7081, 37.6256, 'Ночное такси, работаю круглосуточно', 'Skoda Octavia', 28.0),
        
        # Московская область
        (55.8304, 37.6411, 'Поездки в аэропорт и область', 'Ford Focus', 32.0),
        (55.6761, 37.5775, 'Междугородние поездки', 'Nissan Almera', 27.0),
    ]
    
    for i, (lat, lon, description, car_model, price) in enumerate(test_listings):
        if i < len(driver_ids):
            driver_id = driver_ids[i][0]
            try:
                cursor.execute(
                    'INSERT INTO taxi_listings (driver_id, latitude, longitude, description, car_model, price_per_km, views_count) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (driver_id, lat, lon, description, car_model, price, 0)
                )
                print(f"Добавлено объявление: {car_model} - {description[:30]}...")
            except Exception as e:
                print(f"Ошибка при добавлении объявления: {e}")
    
    # Добавляем тестовые отзывы
    test_reviews = [
        (1, 1, 5, 'Отличный водитель, быстро доехали!'),
        (1, 2, 4, 'Хорошее обслуживание, чистая машина'),
        (2, 1, 5, 'Очень вежливый водитель, рекомендую'),
        (2, 2, 3, 'Нормально, но немного опоздал'),
        (3, 1, 5, 'Премиум сервис, все на высшем уровне!'),
    ]
    
    for listing_id, client_id, rating, comment in test_reviews:
        try:
            cursor.execute(
                'INSERT INTO reviews (listing_id, client_id, rating, comment) VALUES (?, ?, ?, ?)',
                (listing_id, client_id, rating, comment)
            )
            print(f"Добавлен отзыв для объявления {listing_id}")
        except Exception as e:
            print(f"Ошибка при добавлении отзыва: {e}")
    
    conn.commit()
    conn.close()
    print("\nТестовые данные успешно добавлены!")
    print("\nТестовые аккаунты:")
    print("Клиенты: client1/password123, client2/password123")
    print("Водители: driver1/password123, driver2/password123, driver3/password123")

if __name__ == '__main__':
    add_test_data()