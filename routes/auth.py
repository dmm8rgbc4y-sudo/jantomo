# routes/auth.py（PIN認証 + デバイストークン方式）

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, timezone
from models import db
from models.models import User
from models.device import Device
import secrets
from flask_bcrypt import Bcrypt

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

COOKIE_NAME = "device_token"
TOKEN_TTL_DAYS = 30


# ======================================================
# 共通：デバイストークン発行
# ======================================================
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


# ======================================================
# PIN バリデーション
# ======================================================
def _validate_pin(pin: str, redirect_target: str):
    if not pin.isdigit():
        flash('PIN は数字で入力してください。', 'error')
        return redirect(url_for(redirect_target))

    if len(pin) < 4:
        flash('PIN は4桁以上で入力してください。', 'error')
        return redirect(url_for(redirect_target))

    if len(pin) > 6:
        flash('PIN は6桁以下で入力してください。', 'error')
        return redirect(url_for(redirect_target))

    return None


# ======================================================
# 自動ログイン（app.py で before_request に登録する）
# ======================================================
def auto_login():
    if current_user.is_authenticated:
        return

    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return

    device = Device.query.filter_by(token=token, is_revoked=False).first()
    if not device:
        return

    expires_at = device.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    if expires_at and expires_at <= now:
        resp = make_response(redirect(url_for('auth.login')))
        resp.delete_cookie(COOKIE_NAME)
        return resp

    login_user(device.user)


# ======================================================
# LP誘導（app.py で before_request に登録する）
# ======================================================
def force_register_if_not_logged_in():
    if current_user.is_authenticated:
        return

    path = request.path

    allowed_paths = [
        '/register',
        '/login',
        '/static',
        '/__cleanup',
        '/landing',
    ]

    if any(path.startswith(p) for p in allowed_paths):
        return

    return redirect(url_for('main.landing'))


# ======================================================
# 新規登録
# ======================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        pin = request.form.get('pin')

        if not username or not pin:
            flash('ユーザー名と PIN を入力してください。', 'error')
            return redirect(url_for('auth.register'))

        # PIN のバリデーション
        res = _validate_pin(pin, 'auth.register')
        if res:
            return res

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('このユーザー名は既に登録されています。', 'error')
            return redirect(url_for('auth.register'))

        # ★ PIN をハッシュ化して保存
        hashed_pin = bcrypt.generate_password_hash(pin).decode('utf-8')

        new_user = User(username=username, pin=hashed_pin, device_token=None)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        token = _issue_device_token(new_user.id)
        resp = make_response(redirect(url_for('schedule.weekly')))
        _set_login_cookie(resp, token)
        return resp

    return render_template('register.html', mode='register')


# ======================================================
# ログイン
# ======================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        pin = request.form.get('pin')

        if not username or not pin:
            flash('ユーザー名と PIN を入力してください。', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('ユーザーが存在しません。', 'error')
            return redirect(url_for('auth.login'))

        # PIN バリデーション（形式チェックのみ）
        res = _validate_pin(pin, 'auth.login')
        if res:
            return res

        # ★ ハッシュ比較
        if not bcrypt.check_password_hash(user.pin, pin):
            flash('PIN が正しくありません。', 'error')
            return redirect(url_for('auth.login'))

        login_user(user)

        Device.query.filter_by(user_id=user.id, is_revoked=False).update({'is_revoked': True})
        db.session.commit()

        token = _issue_device_token(user.id)
        resp = make_response(redirect(url_for('schedule.weekly')))
        _set_login_cookie(resp, token)
        return resp

    return render_template('register.html', mode='login')


# ======================================================
# ログアウト
# ======================================================
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

    resp = make_response(redirect(url_for('auth.login')))
    resp.delete_cookie(COOKIE_NAME)
    return resp
