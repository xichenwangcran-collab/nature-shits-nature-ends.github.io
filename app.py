"""
Rubbishit Journal — Flask Backend
==================================
Handles: user registration, email verification code sending, login, session.

Requirements:
    pip install flask flask-sqlalchemy flask-mail flask-cors

Configuration:
    Edit MAIL_* settings below to match your email provider.
    Supports: Gmail, QQ Mail, 163 Mail, Outlook, etc.
"""

import os
import random
import string
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///rubbishit.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ─────────────────────────────────────────────
#  EMAIL — edit these before running!
# ─────────────────────────────────────────────
app.config["MAIL_SERVER"]   = "smtp.gmail.com"   # or smtp.qq.com / smtp.163.com
app.config["MAIL_PORT"]     = 587
app.config["MAIL_USE_TLS"]  = True
app.config["MAIL_USERNAME"] = "your_email@gmail.com"   # ← change this
app.config["MAIL_PASSWORD"] = "your_app_password"       # ← change this (App Password)
app.config["MAIL_DEFAULT_SENDER"] = ("Rubbishit Journal", "your_email@gmail.com")
mail = Mail(app)

# ─────────────────────────────────────────────
#  MODELS
# ─────────────────────────────────────────────
class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    verified   = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VerificationCode(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), nullable=False)
    code       = db.Column(db.String(4), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def generate_code():
    """Generate a 4-digit numeric verification code."""
    return str(random.randint(1000, 9999))

def send_verification_email(to_email, code, username):
    """Send HTML verification email."""
    html_body = f"""
    <div style="font-family: Georgia, serif; max-width: 520px; margin: 0 auto;
                border-top: 4px solid #C8102E; padding: 32px 36px; background: #FAF8F3;">
        <div style="font-size: 32px; font-style: italic; font-weight: 900;
                    color: #C8102E; margin-bottom: 4px;">Rubbishit</div>
        <div style="font-size: 11px; color: #888; font-family: monospace;
                    letter-spacing: 0.1em; margin-bottom: 28px;">
            THE JOURNAL OF REJECTED BUT RESILIENT RESEARCH
        </div>
        <p style="color: #333; font-size: 15px; margin-bottom: 20px;">
            Dear <strong>{username}</strong>,
        </p>
        <p style="color: #555; font-size: 14px; line-height: 1.7; margin-bottom: 28px;">
            Welcome to <em>Rubbishit</em> — where no paper is too rejected to find a home.
            Please use the verification code below to complete your registration:
        </p>
        <div style="text-align: center; margin: 28px 0;">
            <div style="display: inline-block; background: #0D0D0D; color: white;
                        font-family: 'Courier New', monospace; font-size: 42px;
                        font-weight: bold; letter-spacing: 18px; padding: 18px 36px 18px 54px;
                        border-radius: 4px;">
                {code}
            </div>
        </div>
        <p style="color: #888; font-size: 12px; text-align: center; margin-bottom: 28px;">
            ⏱ This code expires in <strong>10 minutes</strong>.
        </p>
        <hr style="border: none; border-top: 1px solid #e0dbd0; margin: 24px 0;">
        <p style="color: #aaa; font-size: 11px; font-family: monospace; line-height: 1.7;">
            If you didn't sign up for Rubbishit Journal, please ignore this email.<br>
            Unlike Reviewer 3, we promise not to bother you again.
        </p>
    </div>
    """
    msg = Message(
        subject="[Rubbishit Journal] Your Verification Code: " + code,
        recipients=[to_email],
        html=html_body
    )
    mail.send(msg)

# ─────────────────────────────────────────────
#  ROUTES — API
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/send-code", methods=["POST"])
def send_code():
    """Step 1: Send verification code to email."""
    data = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()

    if not email or "@" not in email:
        return jsonify({"success": False, "message": "请输入有效的邮箱地址"}), 400
    if not username or len(username) < 2:
        return jsonify({"success": False, "message": "用户名至少需要2个字符"}), 400

    # Check if email already registered & verified
    existing = User.query.filter_by(email=email, verified=True).first()
    if existing:
        return jsonify({"success": False, "message": "该邮箱已注册，请直接登录"}), 400

    # Check username taken
    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.verified:
        return jsonify({"success": False, "message": "该用户名已被占用"}), 400

    # Rate limit: max 3 codes per email per hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_codes = VerificationCode.query.filter(
        VerificationCode.email == email,
        VerificationCode.expires_at > one_hour_ago
    ).count()
    if recent_codes >= 3:
        return jsonify({"success": False, "message": "发送次数过多，请1小时后再试"}), 429

    # Generate & save code
    code = generate_code()
    expires = datetime.utcnow() + timedelta(minutes=10)
    vc = VerificationCode(email=email, code=code, expires_at=expires)
    db.session.add(vc)
    db.session.commit()

    # Send email
    try:
        send_verification_email(email, code, username)
        return jsonify({"success": True, "message": f"验证码已发送至 {email}，请查收邮件（有效期10分钟）"})
    except Exception as e:
        db.session.delete(vc)
        db.session.commit()
        return jsonify({"success": False, "message": f"邮件发送失败：{str(e)}"}), 500


@app.route("/api/register", methods=["POST"])
def register():
    """Step 2: Verify code and complete registration."""
    import hashlib
    data     = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    code     = (data.get("code") or "").strip()

    if not all([email, username, password, code]):
        return jsonify({"success": False, "message": "请填写所有必填字段"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "密码至少需要6位"}), 400

    # Find valid code
    vc = VerificationCode.query.filter_by(email=email, code=code, used=False)\
           .filter(VerificationCode.expires_at > datetime.utcnow())\
           .order_by(VerificationCode.id.desc()).first()

    if not vc:
        return jsonify({"success": False, "message": "验证码错误或已过期，请重新获取"}), 400

    # Mark code used
    vc.used = True

    # Create or update user
    user = User.query.filter_by(email=email).first()
    if not user:
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(username=username, email=email, password=pw_hash, verified=True)
        db.session.add(user)
    else:
        user.verified = True
        user.username = username
        user.password = hashlib.sha256(password.encode()).hexdigest()

    db.session.commit()
    session["user_id"] = user.id
    session["username"] = user.username

    return jsonify({"success": True, "message": "注册成功！欢迎加入 Rubbishit Journal 🎉", "username": username})


@app.route("/api/login", methods=["POST"])
def login():
    import hashlib
    data     = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email, verified=True).first()
    if not user:
        return jsonify({"success": False, "message": "邮箱未注册或未完成验证"}), 401

    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if user.password != pw_hash:
        return jsonify({"success": False, "message": "密码错误"}), 401

    session["user_id"] = user.id
    session["username"] = user.username
    return jsonify({"success": True, "message": f"欢迎回来，{user.username}！", "username": user.username})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/me", methods=["GET"])
def me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"logged_in": False})
    user = db.session.get(User, uid)
    if not user:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "username": user.username, "email": user.email})


# ─────────────────────────────────────────────
#  STARTUP
# ─────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database initialised — rubbishit.db")
    print("🚀 Rubbishit Journal running at http://localhost:5000")
    app.run(debug=True, port=5000)
