# routes/auth.py（本番用・デバイス別トークン方式）

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, timezone
from app import db
from models.models import User
from models.device import Device
import secrets

auth_bp = Blueprint('auth', __name__)

COOKIE_NAME = "device_token"
TOKEN_TTL_DAYS = 30


def _issue_device_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=TOKEN_TTL_DAYS)

    device = Device(
        user_id=user_id,
        token=token,
        created_at=now,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.session.add(device)
    db.session.commit()
    return token


def _set_login_cookie(response, token: str):
    secure_flag = not current_app.debug
    max_age = TOKEN_TTL_DAYS * 24 * 60 * 60

    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=secure_flag,
        samesite="Lax",
    )
    return response


# --- 新規登録 ---
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')

        if not username:
            flash('ユーザー名を入力してください。', 'error')
            return redirect(url_for('auth.register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('このユーザー名は既に登録されています。', 'error')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, device_token=secrets.token_hex(16))
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        token = _issue_device_token(new_user.id)
        resp = make_response(redirect(url_for('schedule.weekly')))
        _set_login_cookie(resp, token)

        return resp

    return render_template('register.html', mode='register')


# --- ログイン ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')

        if not username:
            flash('ユーザー名を入力してください。', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('このユーザーは登録されていません。', 'error')
            return redirect(url_for('auth.login'))

        login_user(user)

        Device.query.filter_by(user_id=user.id, is_revoked=False).update({'is_revoked': True})
        db.session.commit()

        token = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(days=TOKEN_TTL_DAYS)
        new_device = Device(user_id=user.id, token=token, expires_at=expires_at, is_revoked=False)
        db.session.add(new_device)
        db.session.commit()

        resp = make_response(redirect(url_for('schedule.weekly')))
        _set_login_cookie(resp, token)

        return resp

    return render_template('register.html', mode='login')


# --- 自動ログイン ---
@auth_bp.before_app_request
def auto_login():
    if current_user.is_authenticated:
        return

    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return

    device = Device.query.filter_by(token=token, is_revoked=False).first()
    if not device:
        return

    now = datetime.utcnow()
    if device.expires_at and device.expires_at > now:
        login_user(device.user)
    else:
        resp = make_response(redirect(url_for('auth.register')))
        resp.delete_cookie(COOKIE_NAME)
        return resp


# --- 未ログインなら強制 /register ---
@auth_bp.before_app_request
def force_register_if_not_logged_in():
    # すでにログイン済みならOK
    if current_user.is_authenticated:
        return

    path = request.path

    # 未ログインでもアクセスOKなパス
    allowed_paths = [
        '/register',
        '/login',
        '/static',   # CSS/JS/画像
        '/__cleanup',  # メンテナンス用
    ]

    # 将来LP実装後に追加
    # allowed_paths.append('/landing')

    # 許可パスならそのまま
    if any(path.startswith(p) for p in allowed_paths):
        return

    # それ以外 → /register に強制
    return redirect(url_for('auth.register'))


# --- ログアウト ---
@auth_bp.route('/logout')
@login_required
def logout():
    token = request.cookies.get(COOKIE_NAME)

    if token:
        device = Device.query.filter_by(token=token, is_revoked=False).first()
        if device:
            device.is_revoked = True
            db.session.commit()

    logout_user()

    flash('ログアウトしました。', 'info')

    resp = make_response(redirect(url_for('auth.register')))
    resp.delete_cookie(COOKIE_NAME)
    return resp
