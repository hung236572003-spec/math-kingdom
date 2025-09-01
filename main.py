from supabase import create_client
import os
import json
from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
import random
from datetime import datetime, timedelta, date
import secrets
import threading
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.permanent_session_lifetime = timedelta(hours=2)

DATA_FILE = "multiplication_data.json"

# Khởi tạo Supabase
supabase = create_client(
    "https://mkgmoefuuslprhwrtyxp.supabase.co",  # URL từ Supabase dashboard
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1rZ21vZWZ1dXNscHJod3J0eXhwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY3MDI0NTEsImV4cCI6MjA3MjI3ODQ1MX0.HXoDcuP32o3f0fHskSHPyhEE4ew_PgTXPLnwMsIkKl0"  # Anon key từ Supabase dashboard
)

def save_data(data):
    """Lưu vào Supabase"""
    supabase.table('app_data').upsert({
        'id': 1,
        'data': json.dumps(data)
    }).execute()

def load_data():
    """Load từ Supabase"""
    try:
        response = supabase.table('app_data').select("*").eq('id', 1).execute()
        if response.data:
            return json.loads(response.data[0]['data'])
    except:
        pass
    
    # Trả về data mặc định
    return get_initial_data()

def save_data(data):
    """Save data vào Deta Base"""
    db.put(data, "main_data", key="value")

def get_initial_data():
    """Trả về dữ liệu mặc định ban đầu"""
    return {
        "users": {
            "123456": {
                "name": "Vy",
                "grade": 2,
                "progress": 2,
                "diamonds": 0,
                "test_history": [],
                "check_history": [],
                "withdrawal_history": [],
                "last_test_date": None
            },
            "4789": {
                "name": "Nga",
                "grade": 3,
                "progress": 2,
                "diamonds": 0,
                "test_history": [],
                "check_history": [],
                "withdrawal_history": [],
                "last_test_date": None
            }
        },
        "admin": {
            "9874": {"name": "Hùng"}
        },
        "messages": [],
        "notifications": [
            {
                "text": "🎉 Chào mừng các em đến với Vương Quốc Toán Học! Hãy cố gắng học tập nhé! 🌟",
                "timestamp": datetime.now().strftime("%d/%m %H:%M"),
                "sender": "Hệ thống"
            }
        ],
        "activity_log": []
    }

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        data = get_initial_data()
        save_data(data)
        return data

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_activity(data, user_name, action):
    """Ghi lại hoạt động để admin biết"""
    activity = {
        "user": user_name,
        "action": action,
        "timestamp": datetime.now().strftime("%d/%m %H:%M:%S")
    }
    if 'activity_log' not in data:
        data['activity_log'] = []
    data['activity_log'].append(activity)
    # Giữ tối đa 50 hoạt động gần nhất
    data['activity_log'] = data['activity_log'][-50:]

def auto_reset_at_midnight():
    """Tự động xóa tin nhắn và hoạt động lúc 00:00"""
    while True:
        now = datetime.now()
        # Tính thời gian đến 00:00
        tomorrow = now + timedelta(days=1)
        midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = (midnight - now).total_seconds()
        
        # Chờ đến 00:00
        time.sleep(seconds_until_midnight)
        
        # Xóa dữ liệu
        data = load_data()
        data['messages'] = []
        data['activity_log'] = []
        
        # Thêm thông báo tự động
        reset_notification = {
            'text': '🌙 Hệ thống đã tự động làm mới tin nhắn và hoạt động lúc 00:00! Chúc các bạn ngủ ngon! 🌟',
            'timestamp': datetime.now().strftime("%d/%m %H:%M"),
            'sender': 'Hệ thống'
        }
        data['notifications'].append(reset_notification)
        data['notifications'] = data['notifications'][-10:]
        
        save_data(data)
        
        # Chờ 1 phút để tránh reset nhiều lần
        time.sleep(60)

# Khởi động thread tự động reset
reset_thread = threading.Thread(target=auto_reset_at_midnight, daemon=True)
reset_thread.start()

def can_take_test(user_data):
    """Kiểm tra xem có thể thi hôm nay không"""
    if not user_data.get('last_test_date'):
        return True
    
    last_test = datetime.fromisoformat(user_data['last_test_date'])
    now = datetime.now()
    
    # Reset vào 12h trưa mỗi ngày
    today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if last_test < today_noon and now >= today_noon:
        return True
    
    # Nếu thi trước 12h hôm qua, có thể thi lại từ 12h hôm nay
    yesterday_noon = today_noon - timedelta(days=1)
    if last_test < yesterday_noon:
        return True
        
    return False

def is_admin_hung():
    """Kiểm tra xem có phải admin Hùng không"""
    return session.get('user') == '9874' and session.get('user_type') == 'admin'

# Base template với responsive design tối ưu cho mobile và desktop
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>✨ Vương Quốc Toán Học Kỳ Diệu ✨</title>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: 'Quicksand', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #ffc0cb 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            animation: gradient 15s ease infinite;
            background-size: 400% 400%;
            position: relative;
            overflow-x: hidden;
            padding: 10px;
        }
        
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .container {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 900px;
            width: 100%;
            backdrop-filter: blur(10px);
            border: 3px solid rgba(255, 255, 255, 0.5);
            position: relative;
            z-index: 10;
        }
        
        /* Mobile responsive */
        @media (max-width: 768px) {
            body {
                padding: 5px;
            }
            
            .container {
                padding: 15px;
                border-radius: 20px;
                width: 100%;
                max-width: 100%;
            }
            
            .header h1 {
                font-size: 1.8em !important;
            }
            
            .menu-grid {
                grid-template-columns: repeat(2, 1fr) !important;
                gap: 10px !important;
            }
            
            .menu-item {
                padding: 15px !important;
            }
            
            .menu-item-icon {
                font-size: 30px !important;
            }
            
            .menu-item-title {
                font-size: 14px !important;
            }
            
            .btn {
                padding: 12px 20px !important;
                font-size: 14px !important;
            }
            
            input[type="password"], input[type="text"], input[type="number"], select, textarea {
                padding: 12px !important;
                font-size: 16px !important;
            }
            
            .diamond-counter {
                position: static !important;
                margin: 10px auto !important;
                display: inline-flex !important;
            }
            
            .question-box {
                font-size: 20px !important;
                padding: 15px !important;
            }
            
            .timer {
                font-size: 20px !important;
                padding: 10px 20px !important;
            }
            
            .chat-container {
                max-height: 300px !important;
            }
            
            .message {
                max-width: 85% !important;
            }
            
            /* Ẩn hiệu ứng cho mobile để tăng performance */
            .floating-hearts, .floating-sparkles, .butterfly, .cloud {
                display: none !important;
            }
        }
        
        /* Tablet responsive */
        @media (min-width: 769px) and (max-width: 1024px) {
            .menu-grid {
                grid-template-columns: repeat(3, 1fr) !important;
            }
            
            .header h1 {
                font-size: 2.2em !important;
            }
        }
        
        /* Desktop optimizations */
        @media (min-width: 1025px) {
            .container {
                padding: 30px;
            }
            
            .menu-grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            position: relative;
        }
        
        .header h1 {
            color: #e91e63;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
            animation: sparkle 2s ease-in-out infinite;
        }
        
        @keyframes sparkle {
            0%, 100% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.05) rotate(2deg); }
        }
        
        .unicorn-icon {
            font-size: 60px;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        .login-form {
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 400px;
            margin: 0 auto;
        }
        
        input[type="password"], input[type="text"], input[type="number"], select, textarea {
            padding: 15px;
            border: 3px solid #f8bbd0;
            border-radius: 20px;
            font-size: 18px;
            font-family: 'Quicksand', sans-serif;
            transition: all 0.3s;
            background: white;
            color: #2d3436;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #e91e63;
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(233, 30, 99, 0.3);
        }
        
        .btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #ff6b9d, #c44569);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            border: none;
            border-radius: 25px;
            font-size: 18px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(233, 30, 99, 0.3);
            font-family: 'Quicksand', sans-serif;
            text-decoration: none;
            display: inline-block;
            position: relative;
            overflow: hidden;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .btn:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(233, 30, 99, 0.4);
            background: linear-gradient(135deg, #ff8fab, #e91e63);
        }
        
        .btn:active {
            transform: translateY(-1px);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ff7675, #d63031);
        }
        
        .btn-danger:hover {
            background: linear-gradient(135deg, #fab1a0, #e17055);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #55efc4, #00b894);
        }
        
        .btn-success:hover {
            background: linear-gradient(135deg, #81ecec, #00cec9);
        }
        
        .btn-warning {
            background: linear-gradient(135deg, #fdcb6e, #f39c12);
        }
        
        .btn-warning:hover {
            background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
        }
        
        .menu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .menu-item {
            background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
            padding: 25px;
            border-radius: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            border: 3px solid transparent;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }
        
        .menu-item::after {
            content: '✨';
            position: absolute;
            top: -20px;
            right: -20px;
            font-size: 40px;
            opacity: 0;
            transition: all 0.3s;
        }
        
        .menu-item:hover::after {
            top: 10px;
            right: 10px;
            opacity: 1;
            animation: twinkle 1s infinite;
        }
        
        .menu-item:hover {
            transform: translateY(-5px) scale(1.05);
            border-color: #e91e63;
            box-shadow: 0 10px 25px rgba(233, 30, 99, 0.3);
        }
        
        .menu-item-icon {
            font-size: 40px;
            margin-bottom: 10px;
            animation: wiggle 2s ease-in-out infinite;
        }
        
        @keyframes wiggle {
            0%, 100% { transform: rotate(0deg); }
            25% { transform: rotate(-5deg); }
            75% { transform: rotate(5deg); }
        }
        
        .menu-item-title {
            font-size: 18px;
            font-weight: bold;
            color: #d63031;
        }
        
        .diamond-counter {
            position: absolute;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            animation: pulse 2s infinite;
        }
        
        .multiplication-display {
            background: linear-gradient(135deg, #fff5f5, #ffe0e0);
            color: #2d3436;
            padding: 30px;
            border-radius: 20px;
            margin: 20px 0;
            font-size: 24px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(233, 30, 99, 0.2);
            font-weight: bold;
            border: 2px solid #ff6b9d;
            position: relative;
            overflow: hidden;
        }
        
        .multiplication-display::before {
            content: '🌟';
            position: absolute;
            top: 10px;
            left: 10px;
            font-size: 20px;
            animation: rotate 3s linear infinite;
        }
        
        .multiplication-display::after {
            content: '🌟';
            position: absolute;
            bottom: 10px;
            right: 10px;
            font-size: 20px;
            animation: rotate 3s linear infinite reverse;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .question-box {
            background: linear-gradient(135deg, #fab1a0, #e17055);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            padding: 25px;
            border-radius: 20px;
            margin: 20px 0;
            font-size: 28px;
            text-align: center;
            animation: pulse 2s infinite;
            position: relative;
        }
        
        .question-box input {
            background: white;
            color: #2d3436;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }
        
        .progress-bar {
            background: #f0f0f0;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b9d, #c44569, #ff6b9d);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            background-size: 200% 100%;
            animation: shimmer 3s linear infinite;
        }
        
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        
        .star {
            color: #ffd700;
            font-size: 30px;
            animation: twinkle 1s ease-in-out infinite;
            display: inline-block;
        }
        
        @keyframes twinkle {
            0%, 100% { 
                opacity: 1; 
                transform: scale(1);
            }
            50% { 
                opacity: 0.5;
                transform: scale(0.8);
            }
        }
        
        .rainbow-text {
            background: linear-gradient(90deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
            font-size: 24px;
            animation: rainbow 5s ease-in-out infinite;
            background-size: 200% 100%;
        }
        
        @keyframes rainbow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .cute-border {
            border: 3px dashed #ff69b4;
            border-radius: 20px;
            padding: 20px;
            margin: 20px 0;
            background: rgba(255, 192, 203, 0.1);
            position: relative;
        }
        
        .cute-border::before {
            content: '🌸';
            position: absolute;
            top: -15px;
            left: 20px;
            background: white;
            padding: 0 5px;
            font-size: 25px;
        }
        
        .cute-border h3 {
            color: #e91e63;
        }
        
        .cute-border p, .cute-border label {
            color: #2d3436;
        }
        
        .floating-hearts {
            position: fixed;
            width: 100%;
            height: 100%;
            pointer-events: none;
            overflow: hidden;
            top: 0;
            left: 0;
            z-index: 1;
        }
        
        .heart {
            position: absolute;
            font-size: 20px;
            animation: float 10s linear infinite;
            color: rgba(255, 105, 180, 0.7);
        }
        
        @keyframes float {
            0% {
                bottom: -10%;
                transform: translateX(0) rotate(0deg);
            }
            100% {
                bottom: 110%;
                transform: translateX(100px) rotate(360deg);
            }
        }
        
        .floating-sparkles {
            position: fixed;
            width: 100%;
            height: 100%;
            pointer-events: none;
            overflow: hidden;
            top: 0;
            left: 0;
            z-index: 2;
        }
        
        .sparkle {
            position: absolute;
            color: rgba(255, 215, 0, 0.8);
            animation: sparkle-fall 8s linear infinite;
        }
        
        @keyframes sparkle-fall {
            0% {
                top: -10%;
                transform: translateX(0) rotate(0deg);
                opacity: 1;
            }
            100% {
                top: 110%;
                transform: translateX(-100px) rotate(720deg);
                opacity: 0;
            }
        }
        
        .success-message {
            background: linear-gradient(135deg, #55efc4, #00b894);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            padding: 20px;
            border-radius: 20px;
            text-align: center;
            font-size: 20px;
            margin: 20px 0;
            animation: slideIn 0.5s ease;
            position: relative;
            overflow: hidden;
        }
        
        .success-message::before {
            content: '🎉';
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 30px;
            animation: bounce 1s infinite;
        }
        
        .success-message::after {
            content: '🎉';
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 30px;
            animation: bounce 1s infinite;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(-100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .error-message {
            background: linear-gradient(135deg, #ff7675, #d63031);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            padding: 20px;
            border-radius: 20px;
            text-align: center;
            font-size: 20px;
            margin: 20px 0;
            animation: shake 0.5s ease;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
            20%, 40%, 60%, 80% { transform: translateX(10px); }
        }
        
        .timer {
            background: linear-gradient(135deg, #fd79a8, #e84393);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            padding: 15px 30px;
            border-radius: 20px;
            font-size: 24px;
            text-align: center;
            margin: 20px auto;
            max-width: 200px;
            box-shadow: 0 5px 15px rgba(232, 67, 147, 0.3);
            animation: pulse 1s infinite;
        }
        
        .wrong-answer {
            background: linear-gradient(135deg, #ff7675, #d63031);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
            font-size: 16px;
        }
        
        .chat-container {
            max-height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 20px;
            margin: 20px 0;
            -webkit-overflow-scrolling: touch;
        }
        
        .message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 15px;
            max-width: 70%;
            animation: messageSlide 0.3s ease;
        }
        
        @keyframes messageSlide {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message-student {
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            margin-right: auto;
        }
        
        .message-admin {
            background: linear-gradient(135deg, #ff6b9d, #c44569);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            margin-left: auto;
        }
        
        .message-header {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .message-time {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .info-text {
            color: #2d3436;
            font-size: 16px;
            margin: 10px 0;
        }
        
        .info-box {
            background: rgba(255, 255, 255, 0.8);
            border: 2px solid #e91e63;
            border-radius: 15px;
            padding: 15px;
            margin: 10px 0;
            color: #2d3436;
            transition: all 0.3s;
        }
        
        .info-box:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(233, 30, 99, 0.2);
        }
        
        .collapsible {
            background-color: #e91e63;
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            cursor: pointer;
            padding: 15px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 16px;
            border-radius: 10px;
            margin: 5px 0;
            transition: 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .collapsible::before {
            content: '';
            position: absolute;
            top: 50%;
            left: -100%;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.2);
            transition: left 0.3s;
        }
        
        .collapsible:hover::before {
            left: 100%;
        }
        
        .collapsible:hover {
            background-color: #c2185b;
        }
        
        .collapsible:after {
            content: '\\002B';
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            float: right;
            margin-left: 5px;
        }
        
        .collapsible.active:after {
            content: "\\2212";
        }
        
        .content {
            padding: 0 18px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.2s ease-out;
            background-color: #f1f1f1;
            border-radius: 0 0 10px 10px;
            margin-top: -5px;
        }
        
        .content.show {
            max-height: 1000px;
            padding: 18px;
        }
        
        .table-display {
            background: linear-gradient(135deg, #fff5f5, #ffe0e0);
            color: #2d3436;
            padding: 15px;
            border-radius: 15px;
            margin: 10px;
            font-weight: bold;
            border: 2px solid #ff69b4;
            transition: all 0.3s;
        }
        
        .table-display:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(255, 105, 180, 0.3);
        }
        
        .table-display h3 {
            color: #e91e63;
        }
        
        .notification-banner {
            background: linear-gradient(135deg, #feca57, #ff9ff3);
            color: #2d3436;
            padding: 15px;
            border-radius: 15px;
            margin: 20px 0;
            font-weight: bold;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            animation: slideIn 0.5s ease;
            position: relative;
            padding-left: 50px;
        }
        
        .notification-banner::before {
            content: '📢';
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 25px;
            animation: shake 2s infinite;
        }
        
        .activity-log {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 15px;
            margin: 10px 0;
            max-height: 300px;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        .activity-item {
            padding: 8px;
            margin: 5px 0;
            background: linear-gradient(135deg, #dfe6e9, #b2bec3);
            border-radius: 8px;
            color: #2d3436;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .activity-item:hover {
            background: linear-gradient(135deg, #b2bec3, #dfe6e9);
            transform: translateX(5px);
        }
        
        .magic-button {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 18px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .magic-button::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 5px;
            height: 5px;
            background: rgba(255, 255, 255, 0.5);
            opacity: 0;
            border-radius: 100%;
            transform: scale(1, 1) translate(-50%);
            transform-origin: 50% 50%;
        }
        
        .magic-button:hover {
            transform: scale(1.1);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.6);
        }
        
        .rainbow-border {
            background: linear-gradient(90deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3);
            padding: 3px;
            border-radius: 20px;
            animation: rainbow 3s linear infinite;
            background-size: 200% 100%;
        }
        
        .rainbow-border-content {
            background: white;
            border-radius: 17px;
            padding: 20px;
        }
        
        .butterfly {
            position: fixed;
            font-size: 30px;
            animation: fly 15s linear infinite;
            pointer-events: none;
            z-index: 5;
        }
        
        @keyframes fly {
            0% {
                left: -50px;
                top: 50%;
                transform: rotate(0deg);
            }
            25% {
                left: 25%;
                top: 20%;
                transform: rotate(45deg);
            }
            50% {
                left: 50%;
                top: 70%;
                transform: rotate(-45deg);
            }
            75% {
                left: 75%;
                top: 30%;
                transform: rotate(90deg);
            }
            100% {
                left: 110%;
                top: 50%;
                transform: rotate(0deg);
            }
        }
        
        .cloud {
            position: fixed;
            background: white;
            border-radius: 100px;
            opacity: 0.7;
            animation: drift 20s infinite;
            pointer-events: none;
            z-index: 1;
        }
        
        .cloud::before,
        .cloud::after {
            content: '';
            position: absolute;
            background: white;
            border-radius: 100px;
        }
        
        .cloud1 {
            width: 100px;
            height: 40px;
            top: 10%;
            left: -100px;
        }
        
        .cloud1::before {
            width: 50px;
            height: 50px;
            top: -25px;
            left: 10px;
        }
        
        .cloud1::after {
            width: 60px;
            height: 40px;
            top: -15px;
            right: 10px;
        }
        
        .cloud2 {
            width: 80px;
            height: 35px;
            top: 25%;
            left: -80px;
            animation-delay: 5s;
        }
        
        .cloud2::before {
            width: 40px;
            height: 40px;
            top: -20px;
            left: 15px;
        }
        
        .cloud2::after {
            width: 50px;
            height: 35px;
            top: -10px;
            right: 15px;
        }
        
        @keyframes drift {
            from {
                transform: translateX(0);
            }
            to {
                transform: translateX(calc(100vw + 200px));
            }
        }
        
        .confetti {
            position: fixed;
            width: 10px;
            height: 10px;
            background: #ff6b9d;
            animation: confetti-fall 3s linear infinite;
            pointer-events: none;
            z-index: 999;
        }
        
        @keyframes confetti-fall {
            0% {
                top: -10px;
                transform: rotate(0deg);
                opacity: 1;
            }
            100% {
                top: 100vh;
                transform: rotate(720deg);
                opacity: 0;
            }
        }
        
        .cute-avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ff9ff3, #feca57);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            margin: 10px auto;
            animation: wiggle 2s infinite;
            box-shadow: 0 5px 15px rgba(255, 159, 243, 0.5);
        }
        
        /* Factory reset warning styles */
        .factory-reset-warning {
            background: linear-gradient(135deg, #ff0000, #8b0000);
            color: #ffd700;  /* Đổi từ white sang màu vàng */
            padding: 30px;
            border-radius: 20px;
            margin: 20px 0;
            border: 5px solid #ffff00;
            animation: warning-pulse 1s infinite;
            position: relative;
        }
        
        @keyframes warning-pulse {
            0%, 100% { 
                box-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
            }
            50% { 
                box-shadow: 0 0 40px rgba(255, 0, 0, 0.8);
            }
        }
        
        .factory-reset-warning h2 {
            font-size: 28px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .factory-reset-warning ul {
            list-style: none;
            padding: 0;
        }
        
        .factory-reset-warning li {
            padding: 10px;
            margin: 5px 0;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            font-size: 18px;
        }
        
        .factory-reset-confirm {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        
        /* Smooth scrolling */
        html {
            scroll-behavior: smooth;
        }
        
        /* Prevent text selection on double tap mobile */
        * {
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
        
        input, textarea {
            -webkit-user-select: text !important;
            -moz-user-select: text !important;
            -ms-user-select: text !important;
            user-select: text !important;
        }
        
        .history-summary {
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            padding: 12px;
            border-radius: 10px;
            margin: 5px 0;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .history-summary:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .delete-section-btn {
            background: linear-gradient(135deg, #ff7675, #d63031);
            color: #2d3436;  /* Đổi từ white sang màu tối */
            font-weight: bold;
            padding: 10px 20px;
            border: none;
            border-radius: 15px;
            font-size: 14px;
            cursor: pointer;
            margin: 10px 0;
            transition: all 0.3s;
        }
        
        .delete-section-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(214, 48, 49, 0.3);
        }
    </style>
</head>
<body>
    <div class="floating-hearts">
        <span class="heart" style="left: 5%; animation-delay: 0s;">💖</span>
        <span class="heart" style="left: 15%; animation-delay: 1s;">💕</span>
        <span class="heart" style="left: 25%; animation-delay: 2s;">💗</span>
        <span class="heart" style="left: 35%; animation-delay: 3s;">💝</span>
        <span class="heart" style="left: 45%; animation-delay: 4s;">💖</span>
        <span class="heart" style="left: 55%; animation-delay: 5s;">💕</span>
        <span class="heart" style="left: 65%; animation-delay: 6s;">💗</span>
        <span class="heart" style="left: 75%; animation-delay: 7s;">💝</span>
        <span class="heart" style="left: 85%; animation-delay: 8s;">💖</span>
        <span class="heart" style="left: 95%; animation-delay: 9s;">💕</span>
    </div>
    
    <div class="floating-sparkles">
        <span class="sparkle" style="left: 10%; animation-delay: 0s; font-size: 20px;">✨</span>
        <span class="sparkle" style="left: 30%; animation-delay: 2s; font-size: 15px;">⭐</span>
        <span class="sparkle" style="left: 50%; animation-delay: 4s; font-size: 25px;">✨</span>
        <span class="sparkle" style="left: 70%; animation-delay: 6s; font-size: 18px;">⭐</span>
        <span class="sparkle" style="left: 90%; animation-delay: 8s; font-size: 22px;">✨</span>
    </div>
    
    <div class="butterfly" style="animation-delay: 0s;">🦋</div>
    <div class="butterfly" style="animation-delay: 7s;">🦋</div>
    
    <div class="cloud cloud1"></div>
    <div class="cloud cloud2"></div>
    
    <div class="container">
'''

HTML_FOOTER = '''
    </div>
    
    <script>
        // Tạo hiệu ứng pháo hoa khi click
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('btn')) {
                // Chỉ tạo confetti trên desktop
                if (window.innerWidth > 768) {
                    for (let i = 0; i < 5; i++) {
                        const confetti = document.createElement('div');
                        confetti.className = 'confetti';
                        confetti.style.left = e.clientX + 'px';
                        confetti.style.top = e.clientY + 'px';
                        confetti.style.background = ['#ff6b9d', '#feca57', '#48dbfb', '#ff9ff3', '#55efc4'][Math.floor(Math.random() * 5)];
                        confetti.style.animationDelay = (i * 0.1) + 's';
                        document.body.appendChild(confetti);
                        setTimeout(() => confetti.remove(), 3000);
                    }
                }
            }
        });
        
        // Prevent zoom on double tap for iOS
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(event) {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Smooth scroll for mobile
        if ('scrollBehavior' in document.documentElement.style) {
            // Browser supports scroll-behavior
        } else {
            // Polyfill for older browsers
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if 'user' in session:
        if session.get('user_type') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    LOGIN_CONTENT = '''
    <div class="header">
        <div class="unicorn-icon">🦄</div>
        <h1>✨ Vương Quốc Toán Học Kỳ Diệu ✨</h1>
        <p class="rainbow-text">Chào mừng bạn đến với thế giới toán học màu nhiệm!</p>
    </div>

    <div class="cute-avatar">👸</div>

    <form class="login-form" method="POST" action="/login">
        <div class="rainbow-border">
            <div class="rainbow-border-content">
                <p style="text-align: center; font-size: 20px; color: #e91e63; margin-bottom: 15px;">
                    🌈 Nhập mật khẩu bí mật của bạn 🌈
                </p>
                <input type="password" name="password" placeholder="Mật khẩu ma thuật..." required>
            </div>
        </div>
        
        <button type="submit" class="magic-button">
            🚀 Bắt Đầu Phiêu Lưu 🚀
        </button>
    </form>

    <div style="text-align: center; margin-top: 30px;">
        <span class="star">⭐</span>
        <span class="star" style="animation-delay: 0.2s;">⭐</span>
        <span class="star" style="animation-delay: 0.4s;">⭐</span>
        <span class="star" style="animation-delay: 0.6s;">⭐</span>
        <span class="star" style="animation-delay: 0.8s;">⭐</span>
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE + LOGIN_CONTENT + HTML_FOOTER)

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    data = load_data()
    
    if password in data['users']:
        session['user'] = password
        session['user_type'] = 'student'
        session.permanent = True
        user_name = data['users'][password]['name']
        log_activity(data, user_name, "Đăng nhập")
        save_data(data)
        return redirect(url_for('dashboard'))
    elif password in data['admin']:
        session['user'] = password
        session['user_type'] = 'admin'
        session.permanent = True
        admin_name = data['admin'][password]['name']
        log_activity(data, admin_name + " (Admin)", "Đăng nhập Admin")
        save_data(data)
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    data = load_data()
    user_data = data['users'][session['user']]
    
    # Hiển thị thông báo từ admin nếu có
    notifications_html = ''
    if data.get('notifications'):
        latest_notification = data['notifications'][-1]  # Lấy thông báo mới nhất
        notifications_html = f'''
        <div class="notification-banner">
            <strong>Thông báo từ {latest_notification.get('sender', 'Admin')}:</strong> {latest_notification['text']}
            <span style="float: right; font-size: 12px;">{latest_notification['timestamp']}</span>
        </div>
        '''
    
    # Tự động mở khóa thi khi hoàn thành bảng 9
    if user_data['progress'] == 9:
        # Kiểm tra xem có bài kiểm tra 10/10 cho bảng 9 chưa
        for check in user_data.get('check_history', []):
            if check['table'] == 9 and check['correct'] == 10:
                user_data['progress'] = 10
                save_data(data)
                break
    
    DASHBOARD_CONTENT = f'''
    {notifications_html}
    
    <div class="header">
        <h1>🌟 Xin chào {user_data['name']}! 🌟</h1>
        <div class="diamond-counter">
            💎 {user_data['diamonds']:.1f} Kim cương
        </div>
    </div>

    <div class="cute-avatar">👸</div>

    <div class="progress-bar">
        <div class="progress-fill" style="width: {(min(user_data['progress'], 9) - 2) * 12.5}%;">
            {"Bảng " + str(user_data['progress']) if user_data['progress'] <= 9 else "Đã hoàn thành"}
        </div>
    </div>

    <div class="menu-grid">
        <a href="/learn" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #ff9ff3, #f368e0);">
                <div class="menu-item-icon">📚</div>
                <div class="menu-item-title">Học Bảng Cửu Chương</div>
            </div>
        </a>
        
        <a href="/check" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #54a0ff, #48dbfb);">
                <div class="menu-item-icon">✏️</div>
                <div class="menu-item-title">Kiểm Tra</div>
            </div>
        </a>
        
        {'<a href="/test" style="text-decoration: none;"><div class="menu-item" style="background: linear-gradient(135deg, #feca57, #ff9ff3);"><div class="menu-item-icon">🏆</div><div class="menu-item-title">Thi Thử</div></div></a>' if user_data['progress'] >= 10 else ''}
        
        <a href="/chat" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #55efc4, #00b894);">
                <div class="menu-item-icon">💬</div>
                <div class="menu-item-title">Nhắn Tin</div>
            </div>
        </a>
        
        <a href="/diamonds" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #00d2d3, #5f27cd);">
                <div class="menu-item-icon">💎</div>
                <div class="menu-item-title">Quản Lý Kim Cương</div>
            </div>
        </a>
        
        <a href="/history" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #ee5a24, #f79f1f);">
                <div class="menu-item-icon">📊</div>
                <div class="menu-item-title">Lịch Sử</div>
            </div>
        </a>
        
        <a href="/tables" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #c44569, #f8b500);">
                <div class="menu-item-icon">📋</div>
                <div class="menu-item-title">Xem Bảng</div>
            </div>
        </a>
        
        <a href="/logout" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #636e72, #2d3436);">
                <div class="menu-item-icon">🚪</div>
                <div class="menu-item-title">Đăng Xuất</div>
            </div>
        </a>
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE + DASHBOARD_CONTENT + HTML_FOOTER)

@app.route('/check', methods=['GET', 'POST'])
def check():
    if 'user' not in session or session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    data = load_data()
    user_data = data['users'][session['user']]
    table = min(user_data['progress'], 9)  # Giới hạn tối đa bảng 9
    
    if request.method == 'GET':
        questions = [(table, i) for i in range(1, 11)]
        random.shuffle(questions)
        session['check_questions'] = questions[:10]
        session['check_start_time'] = datetime.now().isoformat()
        
        CHECK_CONTENT = f'''
        <div class="header">
            <h1>✏️ Kiểm Tra Bảng {table} ✏️</h1>
            <a href="/dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
                ← Quay lại
            </a>
        </div>

        <form method="POST" action="/check" id="checkForm" onsubmit="return validateForm()">
            <div class="cute-border">
        '''
        
        for idx, q in enumerate(session['check_questions']):
            CHECK_CONTENT += f'''
            <div class="question-box">
                <label>Câu {idx + 1}: {q[0]} × {q[1]} = </label>
                <input type="text" name="answer_{idx}" id="answer_{idx}" 
                       style="width: 100px; font-size: 24px; text-align: center;"
                       onkeypress="handleEnterCheck(event, {idx}, 10)">
            </div>
            '''
        
        CHECK_CONTENT += '''
            </div>
            
            <div style="text-align: center;">
                <button type="submit" class="btn">
                    🎯 Nộp Bài 🎯
                </button>
            </div>
        </form>
        
        <script>
            // Focus vào câu đầu tiên
            document.getElementById('answer_0').focus();
            
            function handleEnterCheck(event, currentIndex, totalQuestions) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    
                    // Kiểm tra xem input hiện tại có trống không
                    const currentInput = document.getElementById('answer_' + currentIndex);
                    if (currentInput.value.trim() === '') {
                        alert('Bạn phải nhập đáp án! Không được để trống.');
                        currentInput.focus();
                        return;
                    }
                    
                    // Nếu là câu cuối cùng
                    if (currentIndex === totalQuestions - 1) {
                        // Kiểm tra tất cả câu trước khi submit
                        if (validateForm()) {
                            document.getElementById('checkForm').submit();
                        }
                    } else {
                        // Chuyển sang câu tiếp theo
                        const nextInput = document.getElementById('answer_' + (currentIndex + 1));
                        if (nextInput) {
                            nextInput.focus();
                            nextInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                }
            }
            
            function validateForm() {
                for (let i = 0; i < 10; i++) {
                    const input = document.getElementById('answer_' + i);
                    if (input.value.trim() === '') {
                        alert('Câu ' + (i + 1) + ' chưa có đáp án! Vui lòng nhập đáp án cho tất cả các câu.');
                        input.focus();
                        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        return false;
                    }
                }
                return true;
            }
        </script>
        '''
        
        return render_template_string(HTML_TEMPLATE + CHECK_CONTENT + HTML_FOOTER)
    
    else:
        questions = session.get('check_questions', [])
        correct = 0
        wrong_answers = []
        
        for i, (a, b) in enumerate(questions):
            answer_str = request.form.get(f'answer_{i}', '0').strip()
            if not answer_str:  # Nếu vẫn còn trống (không nên xảy ra)
                answer_str = '0'
            try:
                answer = int(answer_str)
                if answer == a * b:
                    correct += 1
                else:
                    wrong_answers.append({
                        'question': f'{a} × {b}',
                        'correct_answer': a * b,
                        'user_answer': answer
                    })
            except:
                wrong_answers.append({
                    'question': f'{a} × {b}',
                    'correct_answer': a * b,
                    'user_answer': answer_str
                })
        
        check_result = {
            "table": table,
            "correct": correct,
            "total": 10,
            "wrong_answers": wrong_answers,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        user_data["check_history"].append(check_result)
        
        # Log activity
        log_activity(data, user_data['name'], f"Kiểm tra bảng {table}: {correct}/10")
        
        # Tự động nâng cấp nếu đạt 10/10
        if correct == 10 and table < 9:
            user_data["progress"] = table + 1
            save_data(data)
            
            RESULT_CONTENT = f'''
            <div class="success-message">
                🎉 Xuất sắc! Bạn đã mở khóa bảng {table + 1}! 🎉
            </div>
            <div style="text-align: center;">
                <h2 style="color: #00b894;">Kết quả: {correct}/10 ✨</h2>
                <div class="cute-avatar">🎊</div>
                <a href="/dashboard" class="btn" style="margin-top: 20px;">Tiếp tục học</a>
            </div>
            '''
        elif correct == 10 and table == 9:
            # Mở khóa thi khi hoàn thành bảng 9
            user_data["progress"] = 10
            save_data(data)
            
            RESULT_CONTENT = f'''
            <div class="success-message">
                🎊 Tuyệt vời! Bạn đã hoàn thành tất cả bảng cửu chương! 🎊
                <br>Chức năng THI đã được mở khóa!
            </div>
            <div style="text-align: center;">
                <h2 style="color: #00b894;">Kết quả: {correct}/10 🏆</h2>
                <div class="cute-avatar">🏆</div>
                <a href="/test" class="btn" style="margin-top: 20px;">Đi thi ngay!</a>
            </div>
            '''
        else:
            save_data(data)
            
            RESULT_CONTENT = f'''
            <div class="cute-border">
                <h2 style="text-align: center; color: {"#00b894" if correct == 10 else "#e91e63"};">
                    Kết quả: {correct}/10
                </h2>
                <p style="text-align: center; font-size: 20px;">
                    Số câu sai: {10 - correct}
                </p>
            '''
            
            if wrong_answers:
                RESULT_CONTENT += '''
                <button class="collapsible">📝 Xem chi tiết câu sai</button>
                <div class="content">
                '''
                for wrong in wrong_answers:
                    RESULT_CONTENT += f'''
                    <div class="wrong-answer">
                        {wrong['question']} = {wrong['correct_answer']} 
                        (Bạn trả lời: {wrong['user_answer']})
                    </div>
                    '''
                RESULT_CONTENT += '</div>'
            
            RESULT_CONTENT += f'''
            </div>
            <div style="text-align: center; margin-top: 20px;">
                {'<p class="info-text" style="color: #d63031;">Cố gắng lên! Hãy học lại và thử lại nhé! 💪</p>' if correct < 10 else ''}
                <a href="/dashboard" class="btn">Quay lại</a>
            </div>
            
            <script>
                const coll = document.getElementsByClassName("collapsible");
                for (let i = 0; i < coll.length; i++) {{
                    coll[i].addEventListener("click", function() {{
                        this.classList.toggle("active");
                        const content = this.nextElementSibling;
                        content.classList.toggle("show");
                    }});
                }}
            </script>
            '''
        
        return render_template_string(HTML_TEMPLATE + RESULT_CONTENT + HTML_FOOTER)

@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'user' not in session or session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    data = load_data()
    user_data = data['users'][session['user']]
    
    if user_data['progress'] < 10:
        return redirect(url_for('dashboard'))
    
    # Kiểm tra giới hạn 1 lần/ngày
    if not can_take_test(user_data):
        last_test = datetime.fromisoformat(user_data['last_test_date'])
        next_test_time = last_test.replace(hour=12, minute=0, second=0) + timedelta(days=1)
        
        WAIT_CONTENT = f'''
        <div class="header">
            <h1>⏰ Chờ Đến Lượt Thi Tiếp Theo ⏰</h1>
        </div>
        
        <div class="error-message">
            <h2>Bạn đã thi hôm nay rồi!</h2>
            <p>Mỗi ngày chỉ được thi 1 lần</p>
            <p>Thời gian thi tiếp theo: {next_test_time.strftime("%d/%m/%Y lúc 12:00 trưa")}</p>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <a href="/dashboard" class="btn">Quay lại</a>
        </div>
        '''
        return render_template_string(HTML_TEMPLATE + WAIT_CONTENT + HTML_FOOTER)
    
    if request.method == 'GET':
        questions = []
        for table in range(2, 10):  # Bảng 2-9
            for multiplier in range(1, 11):
                questions.append((table, multiplier))
        random.shuffle(questions)
        session['test_questions'] = questions[:80]
        session['test_start_time'] = datetime.now().isoformat()
        
        TEST_CONTENT = f'''
        <div class="header">
            <h1>🏆 Bài Thi Tổng Hợp (Bảng 2-9) 🏆</h1>
            <div class="timer" id="timer">15:00</div>
        </div>

        <form method="POST" action="/test" id="testForm" onsubmit="return validateTestForm()">
            <div class="cute-border">
                <p style="text-align: center; color: #e91e63; font-size: 20px; margin-bottom: 20px;">
                    80 câu - Mỗi câu đúng: 0.1 💎 - Tối đa: 8 💎
                </p>
        '''
        
        for idx, q in enumerate(session['test_questions']):
            TEST_CONTENT += f'''
            <div class="question-box" style="margin: 10px 0;">
                <label>Câu {idx + 1}: {q[0]} × {q[1]} = </label>
                <input type="text" name="answer_{idx}" id="answer_{idx}"
                       style="width: 100px; font-size: 24px; text-align: center;"
                       onkeypress="handleEnterTest(event, {idx}, 80)">
            </div>
            '''
        
        TEST_CONTENT += '''
            </div>
            
            <div style="text-align: center;">
                <button type="submit" class="btn">
                    📝 Nộp Bài Thi 📝
                </button>
            </div>
        </form>

        <script>
            // Focus vào câu đầu tiên
            document.getElementById('answer_0').focus();
            
            let timeLeft = 900;
            const timerElement = document.getElementById('timer');
            const testForm = document.getElementById('testForm');
            
            const timer = setInterval(() => {
                timeLeft--;
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                
                if (timeLeft <= 0) {
                    clearInterval(timer);
                    // Điền 0 cho các câu trống trước khi submit
                    for (let i = 0; i < 80; i++) {
                        const input = document.getElementById('answer_' + i);
                        if (input.value.trim() === '') {
                            input.value = '0';
                        }
                    }
                    testForm.submit();
                }
            }, 1000);
            
            function handleEnterTest(event, currentIndex, totalQuestions) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    
                    // Kiểm tra xem input hiện tại có trống không
                    const currentInput = document.getElementById('answer_' + currentIndex);
                    if (currentInput.value.trim() === '') {
                        alert('Bạn phải nhập đáp án! Không được để trống.');
                        currentInput.focus();
                        return;
                    }
                    
                    // Nếu là câu cuối cùng
                    if (currentIndex === totalQuestions - 1) {
                        if (validateTestForm()) {
                            document.getElementById('testForm').submit();
                        }
                    } else {
                        // Chuyển sang câu tiếp theo
                        const nextInput = document.getElementById('answer_' + (currentIndex + 1));
                        if (nextInput) {
                            nextInput.focus();
                            nextInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                }
            }
            
            function validateTestForm() {
                let hasEmpty = false;
                for (let i = 0; i < 80; i++) {
                    const input = document.getElementById('answer_' + i);
                    if (input.value.trim() === '') {
                        hasEmpty = true;
                        break;
                    }
                }
                
                if (hasEmpty) {
                    if (confirm('Còn câu chưa trả lời! Bạn có muốn tiếp tục không? (Câu trống sẽ được tính là sai)')) {
                        // Điền 0 cho câu trống
                        for (let i = 0; i < 80; i++) {
                            const input = document.getElementById('answer_' + i);
                            if (input.value.trim() === '') {
                                input.value = '0';
                            }
                        }
                        return true;
                    }
                    return false;
                }
                return true;
            }
        </script>
        '''
        
        return render_template_string(HTML_TEMPLATE + TEST_CONTENT + HTML_FOOTER)
    else:
        questions = session.get('test_questions', [])
        correct = 0
        wrong_answers = []
        
        for i, (a, b) in enumerate(questions):
            answer_str = request.form.get(f'answer_{i}', '0').strip()
            if not answer_str:  # Nếu vẫn còn trống
                answer_str = '0'
            try:
                answer = int(answer_str)
                if answer == a * b:
                    correct += 1
                else:
                    wrong_answers.append({
                        'question': f'{a} × {b}',
                        'correct_answer': a * b,
                        'user_answer': answer
                    })
            except:
                wrong_answers.append({
                    'question': f'{a} × {b}',
                    'correct_answer': a * b,
                    'user_answer': answer_str
                })
        
        diamonds_earned = round(correct * 0.1, 1)
        user_data["diamonds"] += diamonds_earned
        user_data["last_test_date"] = datetime.now().isoformat()
        
        test_result = {
            "correct": correct,
            "total": 80,
            "diamonds_earned": diamonds_earned,
            "wrong_answers": wrong_answers[:20],  # Lưu tối đa 20 câu sai
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        user_data["test_history"].append(test_result)
        
        # Log activity
        log_activity(data, user_data['name'], f"Thi: {correct}/80 - Nhận {diamonds_earned} 💎")
        save_data(data)
        
        RESULT_CONTENT = f'''
        <div class="success-message">
            <h2>🎊 Hoàn thành bài thi! 🎊</h2>
            <p style="font-size: 24px;">Số câu đúng: {correct}/80</p>
            <p style="font-size: 24px;">Số câu sai: {80 - correct}</p>
            <p style="font-size: 24px;">Kim cương nhận được: {diamonds_earned} 💎</p>
        </div>
        '''
        
        if wrong_answers:
            RESULT_CONTENT += f'''
            <button class="collapsible">📝 Xem chi tiết {len(wrong_answers)} câu sai</button>
            <div class="content">
            '''
            for wrong in wrong_answers[:20]:
                RESULT_CONTENT += f'''
                <div class="info-box" style="margin: 5px 0;">
                    {wrong['question']} = {wrong['correct_answer']} 
                    (Bạn trả lời: {wrong['user_answer']})
                </div>
                '''
            RESULT_CONTENT += '</div>'
        
        RESULT_CONTENT += '''
        <div style="text-align: center; margin-top: 20px;">
            <a href="/dashboard" class="btn">Quay lại</a>
        </div>
        
        <script>
            const coll = document.getElementsByClassName("collapsible");
            for (let i = 0; i < coll.length; i++) {
                coll[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    const content = this.nextElementSibling;
                    content.classList.toggle("show");
                });
            }
        </script>
        '''
        
        return render_template_string(HTML_TEMPLATE + RESULT_CONTENT + HTML_FOOTER)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    data = load_data()
    admin_name = data['admin'][session['user']]['name']
    
    # Hiển thị hoạt động gần đây với nút xóa CHỈ CHO ADMIN HÙNG
    activity_html = '''
    <div class="activity-log">
        <h3 style="color: #e91e63;">📋 Hoạt động gần đây:</h3>
    '''
    for activity in data.get('activity_log', [])[-10:]:
        activity_html += f'''
        <div class="activity-item">
            <strong>{activity['user']}</strong>: {activity['action']} 
            <span style="float: right; font-size: 12px;">{activity['timestamp']}</span>
        </div>
        '''
    
    # Chỉ hiển thị nút xóa nếu là admin Hùng
    if is_admin_hung():
        activity_html += '''
            <form method="POST" action="/admin/clear_activity">
                <button type="submit" class="delete-section-btn" 
                        onclick="return confirm('Xóa toàn bộ log hoạt động?')">
                    🗑️ Xóa Log Hoạt Động
                </button>
            </form>
        '''
    
    activity_html += '</div>'
    
    ADMIN_CONTENT = f'''
    <div class="header">
        <h1>👑 Quản Trị Viên: {admin_name} 👑</h1>
    </div>
    
    {activity_html}
    
    <div class="menu-grid">
        <a href="/admin/students" style="text-decoration: none;">
            <div class="menu-item">
                <div class="menu-item-icon">👥</div>
                <div class="menu-item-title">Quản Lý Học Sinh</div>
            </div>
        </a>
        
        <a href="/admin/notification" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #feca57, #ff9ff3);">
                <div class="menu-item-icon">📢</div>
                <div class="menu-item-title">Quản Lý Thông Báo</div>
            </div>
        </a>
        
        <a href="/chat" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #55efc4, #00b894);">
                <div class="menu-item-icon">💬</div>
                <div class="menu-item-title">Nhắn Tin</div>
            </div>
        </a>
        
        <a href="/admin/diamonds" style="text-decoration: none;">
            <div class="menu-item">
                <div class="menu-item-icon">💎</div>
                <div class="menu-item-title">Sửa Kim Cương</div>
            </div>
        </a>
        
        <a href="/admin/progress" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #ff9ff3, #f368e0);">
                <div class="menu-item-icon">📈</div>
                <div class="menu-item-title">Sửa Tiến Độ</div>
            </div>
        </a>
        
        <a href="/admin/test_reset" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #74b9ff, #0984e3);">
                <div class="menu-item-icon">🔄</div>
                <div class="menu-item-title">Reset Lượt Thi</div>
            </div>
        </a>
        
        <a href="/admin/passwords" style="text-decoration: none;">
            <div class="menu-item" style="background: linear-gradient(135deg, #54a0ff, #48dbfb);">
                <div class="menu-item-icon">🔑</div>
                <div class="menu-item-title">Đổi Mật Khẩu</div>
            </div>
        </a>
        
        {'<a href="/admin/factory_reset" style="text-decoration: none;"><div class="menu-item" style="background: linear-gradient(135deg, #ff0000, #8b0000);"><div class="menu-item-icon">🔴</div><div class="menu-item-title">FACTORY RESET</div></div></a>' if is_admin_hung() else ''}
        
        <a href="/logout" style="text-decoration: none;">
            <div class="menu-item">
                <div class="menu-item-icon">🚪</div>
                <div class="menu-item-title">Đăng Xuất</div>
            </div>
        </a>
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE + ADMIN_CONTENT + HTML_FOOTER)

@app.route('/admin/clear_activity', methods=['POST'])
def admin_clear_activity():
    if not is_admin_hung():
        return redirect(url_for('admin_dashboard'))
    
    data = load_data()
    data['activity_log'] = []
    save_data(data)
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/notification', methods=['GET', 'POST'])
def admin_notification():
    if 'user' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    data = load_data()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send':
            notification_text = request.form.get('notification', '').strip()
            if notification_text:
                notification = {
                    'text': notification_text,
                    'timestamp': datetime.now().strftime("%d/%m %H:%M"),
                    'sender': data['admin'][session['user']]['name']
                }
                
                if 'notifications' not in data:
                    data['notifications'] = []
                
                data['notifications'].append(notification)
                # Giữ tối đa 10 thông báo
                data['notifications'] = data['notifications'][-10:]
                
                log_activity(data, data['admin'][session['user']]['name'] + " (Admin)", f"Gửi thông báo: {notification_text[:50]}...")
                save_data(data)
                
                SUCCESS_MSG = '<div class="success-message">✅ Đã gửi thông báo cho tất cả học sinh!</div>'
                return render_template_string(HTML_TEMPLATE + SUCCESS_MSG + 
                    '<div style="text-align: center;"><a href="/admin/notification" class="btn">Quay lại</a></div>' + HTML_FOOTER)
        
        elif action == 'delete' and is_admin_hung():
            data['notifications'] = []
            log_activity(data, data['admin'][session['user']]['name'] + " (Admin)", "Xóa toàn bộ thông báo")
            save_data(data)
            
            SUCCESS_MSG = '<div class="success-message">✅ Đã xóa toàn bộ thông báo!</div>'
            return render_template_string(HTML_TEMPLATE + SUCCESS_MSG + 
                '<div style="text-align: center;"><a href="/admin/notification" class="btn">Quay lại</a></div>' + HTML_FOOTER)
    
    NOTIFICATION_CONTENT = '''
    <div class="header">
        <h1>📢 Quản Lý Thông Báo 📢</h1>
        <a href="/admin_dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    
    <div class="rainbow-border">
        <div class="rainbow-border-content">
            <form method="POST">
                <h3 style="color: #e91e63;">Gửi thông báo mới:</h3>
                <textarea name="notification" style="width: 100%; height: 150px; margin: 10px 0;" 
                          placeholder="Nhập nội dung thông báo..."></textarea>
                <input type="hidden" name="action" value="send">
                <button type="submit" class="btn" style="width: 100%;">📤 Gửi Thông Báo</button>
            </form>
        </div>
    </div>
    
    <div class="cute-border">
        <h3>Thông báo đã gửi:</h3>
    '''
    
    for notif in data.get('notifications', [])[-5:]:
        NOTIFICATION_CONTENT += f'''
        <div class="info-box">
            <strong>{notif['sender']}:</strong> {notif['text']}
            <span style="float: right; font-size: 12px;">{notif['timestamp']}</span>
        </div>
        '''
    
    # Chỉ hiển thị nút xóa nếu là admin Hùng
    if is_admin_hung():
        NOTIFICATION_CONTENT += '''
            <form method="POST" style="margin-top: 20px;">
                <input type="hidden" name="action" value="delete">
                <button type="submit" class="btn btn-danger" style="width: 100%;"
                        onclick="return confirm('Bạn có chắc muốn xóa tất cả thông báo?')">
                    🗑️ Xóa Tất Cả Thông Báo
                </button>
            </form>
        '''
    
    NOTIFICATION_CONTENT += '</div>'
    
    return render_template_string(HTML_TEMPLATE + NOTIFICATION_CONTENT + HTML_FOOTER)

@app.route('/admin/factory_reset', methods=['GET', 'POST'])
def admin_factory_reset():
    """Factory Reset - Xóa toàn bộ dữ liệu và tạo lại từ đầu"""
    if not is_admin_hung():
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        confirm_code = request.form.get('confirm_code', '')
        
        if confirm_code == 'RESET2024':
            # Xóa file dữ liệu cũ
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            
            # Tạo lại dữ liệu mặc định
            initial_data = get_initial_data()
            save_data(initial_data)
            
            # Xóa session hiện tại
            session.clear()
            
            SUCCESS_MSG = '''
            <div class="success-message">
                <h2>✅ FACTORY RESET THÀNH CÔNG! ✅</h2>
                <p style="font-size: 20px;">Toàn bộ dữ liệu đã được xóa và khởi tạo lại từ đầu!</p>
                <p style="font-size: 18px;">Web đã trở về trạng thái ban đầu.</p>
            </div>
            
            <div class="cute-avatar">🎉</div>
            
            <div style="text-align: center; margin-top: 20px;">
                <p class="info-text">Bạn cần đăng nhập lại để tiếp tục sử dụng.</p>
                <a href="/" class="magic-button">🏠 Về Trang Đăng Nhập</a>
            </div>
            '''
            return render_template_string(HTML_TEMPLATE + SUCCESS_MSG + HTML_FOOTER)
        else:
            ERROR_MSG = '''
            <div class="error-message">
                ❌ Mã xác nhận không đúng! Vui lòng nhập chính xác: RESET2024
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <a href="/admin/factory_reset" class="btn">Thử lại</a>
            </div>
            '''
            return render_template_string(HTML_TEMPLATE + ERROR_MSG + HTML_FOOTER)
    
    FACTORY_RESET_CONTENT = '''
    <div class="header">
        <h1>🔴 FACTORY RESET - KHÔI PHỤC GỐC 🔴</h1>
        <a href="/admin_dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    
    <div class="factory-reset-warning">
        <h2>⚠️ CẢNH BÁO CỰC KỲ NGHIÊM TRỌNG ⚠️</h2>
        
        <p style="font-size: 20px; text-align: center; margin: 20px 0;">
            🚨 HÀNH ĐỘNG NÀY SẼ XÓA <strong>TOÀN BỘ</strong> MỌI THỨ! 🚨
        </p>
        
        <ul>
            <li>✅ XÓA tất cả tài khoản học sinh và tiến độ</li>
            <li>✅ XÓA tất cả kim cương và lịch sử</li>
            <li>✅ XÓA tất cả tin nhắn và thông báo</li>
            <li>✅ XÓA tất cả hoạt động và dữ liệu</li>
            <li>✅ TẠO LẠI file multiplication_data.json MỚI</li>
            <li>✅ KHÔI PHỤC web về trạng thái BAN ĐẦU</li>
        </ul>
        
        <p style="font-size: 18px; text-align: center; margin: 20px 0; background: rgba(255,255,0,0.2); padding: 10px; border-radius: 10px;">
            ⚡ Sau khi Factory Reset:<br>
            - Tài khoản học sinh: Vy (123456), Nga (4789)<br>
            - Tài khoản admin: Hùng (9874)<br>
            - Tất cả sẽ bắt đầu từ đầu!
        </p>
        
        <div class="factory-reset-confirm">
            <form method="POST" onsubmit="return confirmFactoryReset()">
                <p style="font-size: 18px; color: #ffff00; text-align: center; margin-bottom: 15px;">
                    Để xác nhận, vui lòng nhập mã: <strong style="font-size: 24px;">RESET2024</strong>
                </p>
                
                <input type="text" name="confirm_code" placeholder="Nhập mã xác nhận..." 
                       style="width: 100%; margin-bottom: 15px; text-align: center; font-size: 20px;"
                       autocomplete="off" required>
                
                <button type="submit" class="btn btn-danger" style="width: 100%; font-size: 20px; padding: 20px;">
                    🔴 XÁC NHẬN FACTORY RESET 🔴
                </button>
            </form>
        </div>
    </div>
    
    <div class="info-box" style="margin-top: 20px; background: #fff3cd; border-color: #ffc107;">
        <h3 style="color: #856404;">📌 Lưu ý quan trọng:</h3>
        <p style="color: #856404;">• Hành động này KHÔNG THỂ hoàn tác</p>
        <p style="color: #856404;">• Tất cả người dùng sẽ bị đăng xuất</p>
        <p style="color: #856404;">• Web sẽ như mới cài đặt lần đầu</p>
        <p style="color: #856404;">• Chỉ nên dùng khi thực sự cần thiết</p>
    </div>
    
    <script>
        function confirmFactoryReset() {
            const firstConfirm = confirm('⚠️ Bạn có CHẮC CHẮN muốn FACTORY RESET?\\n\\nTOÀN BỘ dữ liệu sẽ bị XÓA VĨNH VIỄN!');
            
            if (firstConfirm) {
                const secondConfirm = confirm('🔴 ĐÂY LÀ LẦN XÁC NHẬN CUỐI CÙNG! 🔴\\n\\nSau khi bấm OK, KHÔNG THỂ khôi phục lại!\\n\\nBạn vẫn muốn tiếp tục?');
                
                if (secondConfirm) {
                    return true;
                }
            }
            
            return false;
        }
    </script>
    '''
    
    return render_template_string(HTML_TEMPLATE + FACTORY_RESET_CONTENT + HTML_FOOTER)

@app.route('/admin/students', methods=['GET', 'POST'])
def admin_students():
    if 'user' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))

    data = load_data()

    if request.method == 'POST' and is_admin_hung():
        student_pwd = request.form.get('student')
        if student_pwd in data['users']:
            data['users'][student_pwd]['check_history'] = []
            data['users'][student_pwd]['test_history'] = []
            log_activity(data, data['admin'][session['user']]['name'] + " (Admin)",
                         f"Xóa lịch sử {data['users'][student_pwd]['name']}")
            save_data(data)
            return redirect(url_for('admin_students'))

    STUDENTS_CONTENT = '''
    <div class="header">
        <h1>👥 Danh Sách Học Sinh 👥</h1>
        <a href="/admin_dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>

    <div class="cute-border">
    '''

    for pwd, user in data['users'].items():
        progress_text = f"Bảng {user['progress']}" if user['progress'] <= 9 else "Đã hoàn thành"

        # Tổng số kiểm tra và thi
        total_checks = len(user.get('check_history', []))
        total_tests = len(user.get('test_history', []))

        STUDENTS_CONTENT += f'''
        <button class="collapsible">{user['name']} - Lớp {user['grade']} - {user['diamonds']:.1f} 💎</button>
        <div class="content">
            <p class="info-text"><strong>Mật khẩu:</strong> {pwd}</p>
            <p class="info-text"><strong>Tiến độ:</strong> {progress_text}</p>
            <p class="info-text"><strong>Kim cương:</strong> {user['diamonds']:.1f} 💎</p>
            <p class="info-text"><strong>Số lần kiểm tra:</strong> {total_checks}</p>
            <p class="info-text"><strong>Số lần thi:</strong> {total_tests}</p>
        '''

        if is_admin_hung():
            STUDENTS_CONTENT += f'''
            <form method="POST">
                <input type="hidden" name="student" value="{pwd}">
                <button type="submit" class="delete-section-btn"
                        onclick="return confirm('Xóa lịch sử của {user['name']}?')">
                    🗑️ Xóa Lịch Sử
                </button>
            </form>
            '''

        # Hiển thị kiểm tra chi tiết
        if user.get('check_history'):
            STUDENTS_CONTENT += '<h4 style="color: #e91e63; margin-top: 10px;">📝 Lịch sử kiểm tra:</h4>'
            for check in user['check_history'][-5:]:
                STUDENTS_CONTENT += f'''
                <div class="history-summary">
                    📌 Bảng {check['table']} - {check['correct']}/10
                    <br>❌ Sai: {10 - check['correct']} câu
                    <br>🕒 {check['timestamp']}
                '''
                if check.get('wrong_answers'):
                    STUDENTS_CONTENT += f'''
                    <button class="collapsible" style="margin-top: 5px;">Xem chi tiết câu sai</button>
                    <div class="content">
                    '''
                    for w in check['wrong_answers']:
                        STUDENTS_CONTENT += f'<p>• {w["question"]} = {w["correct_answer"]} (bạn: {w["user_answer"]})</p>'
                    STUDENTS_CONTENT += '</div>'
                STUDENTS_CONTENT += '</div>'

        # Hiển thị thi chi tiết
        if user.get('test_history'):
            STUDENTS_CONTENT += '<h4 style="color: #0984e3; margin-top: 10px;">🏆 Lịch sử thi:</h4>'
            for test in user['test_history'][-3:]:
                STUDENTS_CONTENT += f'''
                <div class="history-summary">
                    ✅ {test['correct']}/80
                    <br>❌ Sai: {80 - test['correct']}
                    <br>💎 Được: {test['diamonds_earned']}
                    <br>🕒 {test['timestamp']}
                '''
                if test.get('wrong_answers'):
                    STUDENTS_CONTENT += f'''
                    <button class="collapsible" style="margin-top: 5px;">Xem chi tiết câu sai</button>
                    <div class="content">
                    '''
                    for w in test['wrong_answers'][:10]:
                        STUDENTS_CONTENT += f'<p>• {w["question"]} = {w["correct_answer"]} (bạn: {w["user_answer"]})</p>'
                    STUDENTS_CONTENT += '</div>'
                STUDENTS_CONTENT += '</div>'

        STUDENTS_CONTENT += '</div>'

    STUDENTS_CONTENT += '''
    </div>

    <script>
        const coll = document.getElementsByClassName("collapsible");
        for (let i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                const content = this.nextElementSibling;
                content.classList.toggle("show");
            });
        }
    </script>
    '''

    return render_template_string(HTML_TEMPLATE + STUDENTS_CONTENT + HTML_FOOTER)

@app.route('/history', methods=['GET', 'POST'])
def history():
    if 'user' not in session or session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    data = load_data()
    user_data = data['users'][session['user']]
    
    # Học sinh KHÔNG ĐƯỢC phép xóa lịch sử
    
    HISTORY_CONTENT = f'''
    <div class="header">
        <h1>📊 Lịch Sử Học Tập 📊</h1>
        <a href="/dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    '''
    
    # Lịch sử kiểm tra với collapsible cho chi tiết
    if user_data.get('check_history'):
        HISTORY_CONTENT += '''
        <button class="collapsible">📝 Lịch sử kiểm tra</button>
        <div class="content">
        '''
        for idx, check in enumerate(user_data['check_history'][-10:]):
            HISTORY_CONTENT += f'''
            <div class="history-summary">
                <strong>Bảng {check['table']}:</strong> {check['correct']}/10 điểm
                <br>📅 {check['timestamp']}
                <br>❌ Số câu sai: {10 - check['correct']}
            '''
            if check.get('wrong_answers'):
                HISTORY_CONTENT += f'''
                <button class="collapsible" style="margin-top: 10px; padding: 8px; font-size: 14px;">
                    Xem chi tiết câu sai
                </button>
                <div class="content">
                '''
                for w in check['wrong_answers']:
                    HISTORY_CONTENT += f"<p>• {w['question']} = {w['correct_answer']} (bạn: {w['user_answer']})</p>"
                HISTORY_CONTENT += '</div>'
            HISTORY_CONTENT += '</div>'
        HISTORY_CONTENT += '</div>'
    
    # Lịch sử thi với collapsible cho chi tiết
    if user_data.get('test_history'):
        HISTORY_CONTENT += '''
        <button class="collapsible">🏆 Lịch sử thi</button>
        <div class="content">
        '''
        for test in user_data['test_history'][-10:]:
            HISTORY_CONTENT += f'''
            <div class="history-summary">
                <strong>Điểm:</strong> {test['correct']}/80 câu đúng
                <br>❌ Số câu sai: {80 - test['correct']}
                <br>💎 Kim cương nhận: {test['diamonds_earned']}
                <br>📅 {test['timestamp']}
            '''
            if test.get('wrong_answers'):
                HISTORY_CONTENT += f'''
                <button class="collapsible" style="margin-top: 10px; padding: 8px; font-size: 14px;">
                    Xem chi tiết câu sai
                </button>
                <div class="content">
                '''
                for w in test['wrong_answers'][:10]:
                    HISTORY_CONTENT += f"<p>• {w['question']} = {w['correct_answer']} (bạn: {w['user_answer']})</p>"
                HISTORY_CONTENT += '</div>'
            HISTORY_CONTENT += '</div>'
        HISTORY_CONTENT += '</div>'
    
    # Lịch sử rút kim cương
    if user_data.get('withdrawal_history'):
        HISTORY_CONTENT += '''
        <button class="collapsible">💎 Lịch sử đổi quà</button>
        <div class="content">
        '''
        for withdrawal in user_data['withdrawal_history']:
            HISTORY_CONTENT += f'''
            <div class="info-box">
                📅 {withdrawal['timestamp']}: Đổi 100 💎 thành quà
            </div>
            '''
        HISTORY_CONTENT += '</div>'
    
    # Thống kê tổng quan
    total_checks = len(user_data.get('check_history', []))
    total_tests = len(user_data.get('test_history', []))
    total_withdrawals = len(user_data.get('withdrawal_history', []))
    
    HISTORY_CONTENT += f'''
    <div class="rainbow-border">
        <div class="rainbow-border-content">
            <h3 style="color: #e91e63;">📈 Thống kê tổng quan:</h3>
            <p class="info-text">• Tổng số lần kiểm tra: {total_checks}</p>
            <p class="info-text">• Tổng số lần thi: {total_tests}</p>
            <p class="info-text">• Tổng số lần đổi quà: {total_withdrawals}</p>
            <p class="info-text">• Kim cương hiện tại: {user_data['diamonds']:.1f} 💎</p>
            <p class="info-text">• Tiến độ: {"Bảng " + str(user_data['progress']) if user_data['progress'] <= 9 else "Đã hoàn thành"}</p>
        </div>
    </div>
    
    <script>
        const coll = document.getElementsByClassName("collapsible");
        for (let i = 0; i < coll.length; i++) {{
            coll[i].addEventListener("click", function() {{
                this.classList.toggle("active");
                const content = this.nextElementSibling;
                content.classList.toggle("show");
            }});
        }}
    </script>
    '''
    
    return render_template_string(HTML_TEMPLATE + HISTORY_CONTENT + HTML_FOOTER)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    data = load_data()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send':
            message_text = request.form.get('message', '').strip()
            if message_text:
                if session.get('user_type') == 'student':
                    sender = data['users'][session['user']]['name']
                    sender_type = 'student'
                else:
                    sender = data['admin'][session['user']]['name']
                    sender_type = 'admin'
                
                message = {
                    'sender': sender,
                    'sender_type': sender_type,
                    'text': message_text,
                    'timestamp': datetime.now().strftime("%d/%m %H:%M")
                }
                
                if 'messages' not in data:
                    data['messages'] = []
                
                data['messages'].append(message)
                data['messages'] = data['messages'][-50:]  # Giữ 50 tin nhắn gần nhất
                
                log_activity(data, sender, f"Gửi tin nhắn")
                save_data(data)
                
                return redirect(url_for('chat'))
        
        elif action == 'clear' and is_admin_hung():
            data['messages'] = []
            log_activity(data, data['admin'][session['user']]['name'] + " (Admin)", "Xóa toàn bộ tin nhắn")
            save_data(data)
            return redirect(url_for('chat'))
    
    back_url = '/admin_dashboard' if session.get('user_type') == 'admin' else '/dashboard'
    
    CHAT_CONTENT = f'''
    <div class="header">
        <h1>💬 Phòng Chat 💬</h1>
        <a href="{back_url}" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    '''
    
    # Chỉ hiển thị nút xóa nếu là admin Hùng
    if is_admin_hung():
        CHAT_CONTENT += '<form method="POST"><input type="hidden" name="action" value="clear"><button type="submit" class="delete-section-btn" onclick="return confirm(\'Xóa toàn bộ tin nhắn?\')">🗑️ Xóa Toàn Bộ Tin Nhắn</button></form>'
    
    CHAT_CONTENT += '<div class="chat-container">'
    
    for msg in data.get('messages', [])[-20:]:
        msg_class = 'message-admin' if msg['sender_type'] == 'admin' else 'message-student'
        CHAT_CONTENT += f'''
        <div class="message {msg_class}">
            <div class="message-header">{msg['sender']}</div>
            <div>{msg['text']}</div>
            <div class="message-time">{msg['timestamp']}</div>
        </div>
        '''
    
    CHAT_CONTENT += '''
    </div>
    
    <form method="POST" style="margin-top: 20px;">
        <input type="hidden" name="action" value="send">
        <div style="display: flex; gap: 10px;">
            <input type="text" name="message" placeholder="Nhập tin nhắn..." 
                   style="flex: 1;" required autofocus>
            <button type="submit" class="magic-button">📤 Gửi</button>
        </div>
    </form>
    '''
    
    return render_template_string(HTML_TEMPLATE + CHAT_CONTENT + HTML_FOOTER)

# Các route còn lại giữ nguyên...
@app.route('/admin/passwords', methods=['GET', 'POST'])
def admin_passwords():
    if 'user' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    data = load_data()
    
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        old_pwd = request.form.get('old_password')
        new_pwd = request.form.get('new_password')
        
        # Kiểm tra mật khẩu mới có trùng không
        if new_pwd in data['users'] or new_pwd in data['admin']:
            ERROR_MSG = f'<div class="error-message">❌ Lỗi: Mật khẩu "{new_pwd}" đã tồn tại! Vui lòng chọn mật khẩu khác.</div>'
            return render_template_string(HTML_TEMPLATE + ERROR_MSG + 
                '<div style="text-align: center;"><a href="/admin/passwords" class="btn">Thử lại</a></div>' + HTML_FOOTER)
        
        # Kiểm tra mật khẩu mới trùng với mật khẩu cũ
        if new_pwd == old_pwd:
            ERROR_MSG = '<div class="error-message">❌ Lỗi: Mật khẩu mới không được trùng với mật khẩu cũ!</div>'
            return render_template_string(HTML_TEMPLATE + ERROR_MSG + 
                '<div style="text-align: center;"><a href="/admin/passwords" class="btn">Thử lại</a></div>' + HTML_FOOTER)
        
        if user_type == 'student' and old_pwd in data['users']:
            user_data = data['users'].pop(old_pwd)
            data['users'][new_pwd] = user_data
            log_activity(data, data['admin'][session['user']]['name'] + " (Admin)", 
                       f"Đổi mật khẩu cho {user_data['name']}")
            save_data(data)
            
            SUCCESS_MSG = f'<div class="success-message">✅ Đã đổi mật khẩu cho {user_data["name"]}! Mật khẩu mới: {new_pwd}</div>'
            return render_template_string(HTML_TEMPLATE + SUCCESS_MSG + 
                '<div style="text-align: center;"><a href="/admin/passwords" class="btn">Quay lại</a></div>' + HTML_FOOTER)
        
        elif user_type == 'admin' and old_pwd in data['admin']:
            admin_data = data['admin'].pop(old_pwd)
            data['admin'][new_pwd] = admin_data
            log_activity(data, data['admin'][session['user']]['name'] + " (Admin)", 
                       f"Đổi mật khẩu admin {admin_data['name']}")
            save_data(data)
            
            if old_pwd == session['user']:
                session['user'] = new_pwd
            
            SUCCESS_MSG = f'<div class="success-message">✅ Đã đổi mật khẩu admin! Mật khẩu mới: {new_pwd}</div>'
            return render_template_string(HTML_TEMPLATE + SUCCESS_MSG + 
                '<div style="text-align: center;"><a href="/admin/passwords" class="btn">Quay lại</a></div>' + HTML_FOOTER)
    
    PASSWORD_CONTENT = '''
    <div class="header">
        <h1>🔑 Đổi Mật Khẩu 🔑</h1>
        <a href="/admin_dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    
    <form method="POST" class="cute-border">
        <h3>Đổi mật khẩu người dùng:</h3>
        
        <label>Loại tài khoản:</label>
        <select name="user_type" id="userType" onchange="updateUserList()" required>
            <option value="">-- Chọn loại --</option>
            <option value="student">Học sinh</option>
            <option value="admin">Admin</option>
        </select>
        
        <label style="margin-top: 10px;">Mật khẩu cũ:</label>
        <select name="old_password" id="oldPassword" required>
            <option value="">-- Chọn người dùng --</option>
        </select>
        
        <label style="margin-top: 10px;">Mật khẩu mới:</label>
        <input type="text" name="new_password" required placeholder="Nhập mật khẩu mới..." minlength="3">
        
        <button type="submit" class="btn" style="width: 100%; margin-top: 15px;">
            🔐 Đổi mật khẩu
        </button>
    </form>
    
    <div class="info-box" style="margin-top: 20px;">
        <h4 style="color: #e91e63;">⚠️ Lưu ý:</h4>
        <p>• Mật khẩu mới không được trùng với mật khẩu hiện có</p>
        <p>• Mật khẩu mới không được trùng với mật khẩu cũ</p>
        <p>• Độ dài tối thiểu 3 ký tự</p>
    </div>
    
    <script>
        const students = {
    '''
    
    for pwd, user in data['users'].items():
        PASSWORD_CONTENT += f'"{pwd}": "{user["name"]} (MK: {pwd})",\n'
    
    PASSWORD_CONTENT += '''
        };
        
        const admins = {
    '''
    
    for pwd, admin in data['admin'].items():
        PASSWORD_CONTENT += f'"{pwd}": "{admin["name"]} (MK: {pwd})",\n'
    
    PASSWORD_CONTENT += '''
        };
        
        function updateUserList() {
            const userType = document.getElementById('userType').value;
            const oldPassword = document.getElementById('oldPassword');
            
            oldPassword.innerHTML = '<option value="">-- Chọn người dùng --</option>';
            
            if (userType === 'student') {
                for (const [pwd, name] of Object.entries(students)) {
                    oldPassword.innerHTML += `<option value="${pwd}">${name}</option>`;
                }
            } else if (userType === 'admin') {
                for (const [pwd, name] of Object.entries(admins)) {
                    oldPassword.innerHTML += `<option value="${pwd}">${name}</option>`;
                }
            }
        }
    </script>
    '''
    
    return render_template_string(HTML_TEMPLATE + PASSWORD_CONTENT + HTML_FOOTER)

# Các route còn lại giữ nguyên như code gốc...
@app.route('/learn')
def learn():
    if 'user' not in session or session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    data = load_data()
    user_data = data['users'][session['user']]
    table = min(user_data['progress'], 9)
    
    LEARN_CONTENT = f'''
    <div class="header">
        <h1>📚 Học Bảng {table} 📚</h1>
        <a href="/dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>

    <div class="cute-border">
    '''
    
    for i in range(1, 11):
        LEARN_CONTENT += f'''
        <div class="multiplication-display" style="animation-delay: {i * 0.1}s;">
            {table} × {i} = {table * i}
        </div>
        '''
    
    LEARN_CONTENT += '''
    </div>

    <div style="text-align: center; margin-top: 30px;">
        <a href="/check" class="magic-button">
            ✅ Kiểm Tra Ngay!
        </a>
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE + LEARN_CONTENT + HTML_FOOTER)

@app.route('/tables')
def tables():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    back_url = '/admin_dashboard' if session.get('user_type') == 'admin' else '/dashboard'
    
    TABLES_CONTENT = f'''
    <div class="header">
        <h1>📋 Bảng Cửu Chương 📋</h1>
        <a href="{back_url}" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
    '''
    
    colors = ['#ff6b9d', '#c44569', '#0984e3', '#00b894', '#fdcb6e', '#e17055', '#a29bfe', '#fd79a8']
    
    for table in range(2, 10):
        TABLES_CONTENT += f'''
        <div class="table-display">
            <h3 style="text-align: center; color: {colors[table-2]}; margin-bottom: 15px; font-size: 24px;">
                🌟 Bảng {table} 🌟
            </h3>
        '''
        for i in range(1, 11):
            TABLES_CONTENT += f'''
            <div style="color: #2d3436; padding: 5px; font-weight: bold; font-size: 18px;">
                {table} × {i} = {table * i}
            </div>
            '''
        TABLES_CONTENT += '''
        </div>
        '''
    
    TABLES_CONTENT += '''
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE + TABLES_CONTENT + HTML_FOOTER)

@app.route('/diamonds')
def diamonds():
    if 'user' not in session or session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    data = load_data()
    user_data = data['users'][session['user']]
    
    DIAMONDS_CONTENT = f'''
    <div class="header">
        <h1>💎 Quản Lý Kim Cương 💎</h1>
        <a href="/dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    
    <div class="rainbow-border">
        <div class="rainbow-border-content" style="text-align: center;">
            <h2 style="color: #0984e3;">Số kim cương hiện tại</h2>
            <p style="font-size: 48px; font-weight: bold; color: #00b894;">
                💎 {user_data['diamonds']:.1f}
            </p>
        </div>
    </div>
    
    <div class="cute-border">
        <h3 style="color: #e91e63;">📜 Quy tắc đổi quà:</h3>
        <p class="info-text">• Đạt 100 💎 có thể đổi quà</p>
        <p class="info-text">• Mỗi bài thi (80 câu): tối đa 8 💎</p>
        <p class="info-text">• Mỗi ngày chỉ thi 1 lần</p>
        <p class="info-text">• Kim cương không mất khi đăng xuất</p>
    </div>
    
    {'<div style="text-align: center; margin: 20px 0;"><a href="/withdraw" class="magic-button">🎁 Đổi Quà (100 💎) 🎁</a></div>' if user_data['diamonds'] >= 100 else '<div class="error-message">Cần đủ 100 💎 để đổi quà</div>'}
    
    <div class="cute-border">
        <h3 style="color: #e91e63;">📊 Lịch sử đổi quà:</h3>
    '''
    
    if user_data.get('withdrawal_history'):
        for withdrawal in user_data['withdrawal_history'][-5:]:
            DIAMONDS_CONTENT += f'''
            <div class="info-box">
                {withdrawal['timestamp']}: Đổi 100 💎
            </div>
            '''
    else:
        DIAMONDS_CONTENT += '<p class="info-text">Chưa có lịch sử đổi quà</p>'
    
    DIAMONDS_CONTENT += '''
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE + DIAMONDS_CONTENT + HTML_FOOTER)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user' not in session or session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    data = load_data()
    user_data = data['users'][session['user']]
    
    if user_data['diamonds'] < 100:
        return redirect(url_for('diamonds'))
    
    if request.method == 'POST':
        user_data['diamonds'] -= 100
        withdrawal = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        user_data['withdrawal_history'].append(withdrawal)
        
        log_activity(data, user_data['name'], "Đổi 100 💎")
        save_data(data)
        
        SUCCESS_CONTENT = f'''
        <div class="success-message">
            <h2>🎊 Chúc mừng! 🎊</h2>
            <p>Bạn đã đổi thành công 100 💎!</p>
            <p>Kim cương còn lại: {user_data['diamonds']:.1f} 💎</p>
        </div>
        <div class="cute-avatar">🎁</div>
        <div style="text-align: center;">
            <a href="/diamonds" class="btn">Quay lại</a>
        </div>
        '''
        return render_template_string(HTML_TEMPLATE + SUCCESS_CONTENT + HTML_FOOTER)
    
    WITHDRAW_CONTENT = f'''
    <div class="header">
        <h1>🎁 Xác Nhận Đổi Quà 🎁</h1>
    </div>
    
    <div class="rainbow-border">
        <div class="rainbow-border-content" style="text-align: center;">
            <h2 style="color: #e91e63;">Bạn có chắc muốn đổi 100 💎?</h2>
            <p class="info-text">Kim cương hiện tại: {user_data['diamonds']:.1f} 💎</p>
            <p class="info-text">Sau khi đổi: {user_data['diamonds'] - 100:.1f} 💎</p>
            
            <form method="POST" style="margin-top: 20px;">
                <button type="submit" class="btn btn-success">✅ Xác nhận đổi quà</button>
            </form>
            
            <a href="/diamonds" class="btn btn-danger" style="margin-top: 10px;">❌ Hủy bỏ</a>
        </div>
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE + WITHDRAW_CONTENT + HTML_FOOTER)

@app.route('/admin/diamonds', methods=['GET', 'POST'])
def admin_diamonds():
    if 'user' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    data = load_data()
    
    if request.method == 'POST':
        student_pwd = request.form.get('student')
        new_diamonds = request.form.get('diamonds')
        
        if student_pwd in data['users']:
            try:
                data['users'][student_pwd]['diamonds'] = float(new_diamonds)
                log_activity(data, data['admin'][session['user']]['name'] + " (Admin)", 
                           f"Sửa kim cương {data['users'][student_pwd]['name']}: {new_diamonds}")
                save_data(data)
                
                SUCCESS_MSG = f'<div class="success-message">✅ Đã cập nhật kim cương cho {data["users"][student_pwd]["name"]}!</div>'
                return render_template_string(HTML_TEMPLATE + SUCCESS_MSG + 
                    '<div style="text-align: center;"><a href="/admin/diamonds" class="btn">Quay lại</a></div>' + HTML_FOOTER)
            except:
                pass
    
    DIAMONDS_CONTENT = '''
    <div class="header">
        <h1>💎 Quản Lý Kim Cương 💎</h1>
        <a href="/admin_dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    
    <form method="POST" class="cute-border">
        <h3>Chỉnh sửa kim cương:</h3>
        
        <label>Chọn học sinh:</label>
        <select name="student" required>
            <option value="">-- Chọn học sinh --</option>
    '''
    
    for pwd, user in data['users'].items():
        DIAMONDS_CONTENT += f'<option value="{pwd}">{user["name"]} (Hiện tại: {user["diamonds"]:.1f} 💎)</option>'
    
    DIAMONDS_CONTENT += '''
        </select>
        
        <label style="margin-top: 10px;">Số kim cương mới:</label>
        <input type="number" name="diamonds" step="0.1" min="0" required>
        
        <button type="submit" class="btn" style="width: 100%; margin-top: 15px;">
            💾 Lưu thay đổi
        </button>
    </form>
    '''
    
    return render_template_string(HTML_TEMPLATE + DIAMONDS_CONTENT + HTML_FOOTER)

@app.route('/admin/progress', methods=['GET', 'POST'])
def admin_progress():
    if 'user' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    data = load_data()
    
    if request.method == 'POST':
        student_pwd = request.form.get('student')
        new_progress = request.form.get('progress')
        
        if student_pwd in data['users']:
            try:
                data['users'][student_pwd]['progress'] = int(new_progress)
                log_activity(data, data['admin'][session['user']]['name'] + " (Admin)", 
                           f"Sửa tiến độ {data['users'][student_pwd]['name']}: Bảng {new_progress}")
                save_data(data)
                
                SUCCESS_MSG = f'<div class="success-message">✅ Đã cập nhật tiến độ cho {data["users"][student_pwd]["name"]}!</div>'
                return render_template_string(HTML_TEMPLATE + SUCCESS_MSG + 
                    '<div style="text-align: center;"><a href="/admin/progress" class="btn">Quay lại</a></div>' + HTML_FOOTER)
            except:
                pass
    
    PROGRESS_CONTENT = '''
    <div class="header">
        <h1>📈 Quản Lý Tiến Độ 📈</h1>
        <a href="/admin_dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    
    <form method="POST" class="cute-border">
        <h3>Chỉnh sửa tiến độ học:</h3>
        
        <label>Chọn học sinh:</label>
        <select name="student" required>
            <option value="">-- Chọn học sinh --</option>
    '''
    
    for pwd, user in data['users'].items():
        current = f"Bảng {user['progress']}" if user['progress'] <= 9 else "Đã hoàn thành (10)"
        PROGRESS_CONTENT += f'<option value="{pwd}">{user["name"]} (Hiện tại: {current})</option>'
    
    PROGRESS_CONTENT += '''
        </select>
        
        <label style="margin-top: 10px;">Tiến độ mới:</label>
        <select name="progress" required>
            <option value="2">Bảng 2</option>
            <option value="3">Bảng 3</option>
            <option value="4">Bảng 4</option>
            <option value="5">Bảng 5</option>
            <option value="6">Bảng 6</option>
            <option value="7">Bảng 7</option>
            <option value="8">Bảng 8</option>
            <option value="9">Bảng 9</option>
            <option value="10">Đã hoàn thành (Mở khóa thi)</option>
        </select>
        
        <button type="submit" class="btn" style="width: 100%; margin-top: 15px;">
            💾 Lưu thay đổi
        </button>
    </form>
    '''
    
    return render_template_string(HTML_TEMPLATE + PROGRESS_CONTENT + HTML_FOOTER)

@app.route('/admin/test_reset', methods=['GET', 'POST'])
def admin_test_reset():
    if 'user' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    data = load_data()
    
    if request.method == 'POST':
        student_pwd = request.form.get('student')
        
        if student_pwd in data['users']:
            data['users'][student_pwd]['last_test_date'] = None
            log_activity(data, data['admin'][session['user']]['name'] + " (Admin)", 
                       f"Reset lượt thi cho {data['users'][student_pwd]['name']}")
            save_data(data)
            
            SUCCESS_MSG = f'<div class="success-message">✅ Đã reset lượt thi cho {data["users"][student_pwd]["name"]}!</div>'
            return render_template_string(HTML_TEMPLATE + SUCCESS_MSG + 
                '<div style="text-align: center;"><a href="/admin/test_reset" class="btn">Quay lại</a></div>' + HTML_FOOTER)
    
    RESET_CONTENT = '''
    <div class="header">
        <h1>🔄 Reset Lượt Thi 🔄</h1>
        <a href="/admin_dashboard" class="btn" style="position: absolute; top: 20px; left: 20px;">
            ← Quay lại
        </a>
    </div>
    
    <form method="POST" class="cute-border">
        <h3>Reset lượt thi trong ngày:</h3>
        <p class="info-text">Cho phép học sinh thi lại ngay lập tức</p>
        
        <label>Chọn học sinh:</label>
        <select name="student" required>
            <option value="">-- Chọn học sinh --</option>
    '''
    
    for pwd, user in data['users'].items():
        last_test = "Chưa thi" if not user.get('last_test_date') else user['last_test_date'][:16]
        RESET_CONTENT += f'<option value="{pwd}">{user["name"]} (Thi lần cuối: {last_test})</option>'
    
    RESET_CONTENT += '''
        </select>
        
        <button type="submit" class="btn" style="width: 100%; margin-top: 15px;">
            🔄 Reset lượt thi
        </button>
    </form>
    '''
    
    return render_template_string(HTML_TEMPLATE + RESET_CONTENT + HTML_FOOTER)

@app.route('/logout')
def logout():
    if 'user' in session:
        data = load_data()
        if session.get('user_type') == 'student':
            user_name = data['users'][session['user']]['name']
        else:
            user_name = data['admin'][session['user']]['name'] + " (Admin)"
        log_activity(data, user_name, "Đăng xuất")
        save_data(data)
    
    session.clear()
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    ERROR_CONTENT = '''
    <div class="header">
        <h1>😢 Lỗi 404 - Không tìm thấy trang 😢</h1>
    </div>
    
    <div class="error-message">
        <p>Trang bạn tìm kiếm không tồn tại!</p>
    </div>
    
    <div class="cute-avatar">😭</div>
    
    <div style="text-align: center; margin-top: 20px;">
        <a href="/" class="magic-button">🏠 Về Trang Chủ</a>
    </div>
    '''
    return render_template_string(HTML_TEMPLATE + ERROR_CONTENT + HTML_FOOTER), 404

@app.errorhandler(500)
def internal_error(e):
    ERROR_CONTENT = '''
    <div class="header">
        <h1>😰 Lỗi 500 - Lỗi máy chủ 😰</h1>
    </div>
    
    <div class="error-message">
        <p>Có lỗi xảy ra! Vui lòng thử lại sau.</p>
    </div>
    
    <div class="cute-avatar">🤕</div>
    
    <div style="text-align: center; margin-top: 20px;">
        <a href="/" class="magic-button">🏠 Về Trang Chủ</a>
    </div>
    '''
    return render_template_string(HTML_TEMPLATE + ERROR_CONTENT + HTML_FOOTER), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)