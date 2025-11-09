from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from app import db
from models.friend import Friend
from models.models import User  # Userテーブルを参照

# Blueprint設定
friend_bp = Blueprint('friend', __name__)

# ==========================================
# 👥 友達一覧ページ
# ==========================================
@friend_bp.route('/friends')
@login_required
def friend_list():
    """
    承認済みの友達一覧を表示。
    """
    try:
        # Friendテーブルから承認済みフレンドIDを取得
        friend_ids = Friend.get_friend_ids(current_user.id)

        # 該当ユーザー情報をUserテーブルから取得
        friends = User.query.filter(User.id.in_(friend_ids)).all()

    except Exception as e:
        db.session.rollback()
        flash("友達情報の取得に失敗しました。", "error")
        friends = []

    return render_template('friends.html', friends=friends)

# ==========================================
# 🗑️ 友達削除処理
# ==========================================
from flask import request, redirect, url_for

@friend_bp.route('/friend/delete', methods=['POST'])
@login_required
def friend_delete():
    """
    友達関係を削除する。
    双方向のどちら側に自分がいても削除できるようにする。
    """
    target_id = request.form.get('friend_id')

    if not target_id:
        flash("削除対象が指定されていません。", "error")
        return redirect(url_for('friend.friend_list'))

    # 双方向で検索
    relation = Friend.query.filter(
        db.or_(
            db.and_(Friend.user_id == current_user.id, Friend.friend_id == target_id),
            db.and_(Friend.user_id == target_id, Friend.friend_id == current_user.id)
        )
    ).first()

    if not relation:
        flash("友達関係が見つかりません。", "error")
        return redirect(url_for('friend.friend_list'))

    # 削除実行
    db.session.delete(relation)
    db.session.commit()

    flash("友達を削除しました。", "info")
    return redirect(url_for('friend.friend_list'))


# ==========================================
# ➕ 友達申請ページ
# ==========================================
from flask import request, redirect, url_for

@friend_bp.route('/friend/request', methods=['GET', 'POST'])
@login_required
def friend_request():
    if request.method == 'POST':
        target_name = request.form.get('username')

        if not target_name:
            flash("ユーザー名を入力してください。", "error")
            return redirect(url_for('friend.friend_request'))

        # --- 対象ユーザーを検索 ---
        target_user = User.query.filter_by(username=target_name).first()

        if not target_user:
            flash("ユーザーが見つかりません。", "error")
            return redirect(url_for('friend.friend_request'))

        # --- 自分自身は申請できない ---
        if target_user.id == current_user.id:
            flash("自分自身には申請できません。", "error")
            return redirect(url_for('friend.friend_request'))

        # --- 既にフレンド関係がある場合を確認 ---
        existing = Friend.query.filter(
            db.or_(
                db.and_(Friend.user_id == current_user.id, Friend.friend_id == target_user.id),
                db.and_(Friend.user_id == target_user.id, Friend.friend_id == current_user.id)
            )
        ).first()

        if existing:
            flash("既にフレンド登録されています。", "info")
            return redirect(url_for('friend.friend_request'))

        # --- Friend登録（MVP: pendingで申請待ち状態に）---
        new_friend = Friend(user_id=current_user.id, friend_id=target_user.id, status='pending')
        db.session.add(new_friend)
        db.session.commit()

        flash(f"{target_user.username} さんに友達申請を送りました！", "success")
        return redirect(url_for('friend.friend_list'))

    return render_template('friend_request.html')

# ==========================================
# 📬 友達申請受領ページ（inbox）
# ==========================================
from flask import request, redirect, url_for, jsonify

@friend_bp.route('/friend/inbox', methods=['GET', 'POST'])
@login_required
def friend_inbox():
    """
    自分宛てに届いた友達申請一覧を表示し、
    承認または拒否を処理する。
    """
    if request.method == 'POST':
        action = request.form.get('action')
        from_user_id = request.form.get('from_user_id')

        # 申請元を検索
        target_friend = Friend.query.filter_by(
            user_id=from_user_id,
            friend_id=current_user.id,
            status='pending'
        ).first()

        if not target_friend:
            flash("対象データが見つかりません。", "error")
            return redirect(url_for('friend.friend_inbox'))

        if action == 'accept':
            target_friend.status = 'accepted'
            flash("友達申請を承認しました！", "success")
        elif action == 'reject':
            db.session.delete(target_friend)
            flash("友達申請を拒否しました。", "info")

        db.session.commit()
        return redirect(url_for('friend.friend_inbox'))

    # --- 承認待ち（pending）の申請一覧を取得 ---
    requests = Friend.query.filter_by(friend_id=current_user.id, status='pending').all()

    # --- 申請元ユーザー情報を取得 ---
    request_data = []
    for r in requests:
        from_user = User.query.get(r.user_id)
        if from_user:
            request_data.append(from_user)

    return render_template('friend_inbox.html', requests=request_data)

@friend_bp.route("/pending-count")
@login_required
def pending_count():
    from models.friend_request import FriendRequest
    count = FriendRequest.query.filter_by(
        to_user_id=current_user.id, status="pending"
    ).count()
    return jsonify({"count": count})
