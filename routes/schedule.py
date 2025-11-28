from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import date, timedelta
from flask_login import login_required, current_user
from models import db
from models import Schedule
from models.friend import Friend   # 友達機能利用予定
import json

schedule_bp = Blueprint('schedule', __name__)

def get_week_dates(start_date):
    """指定日を含む週の7日分を返す"""
    monday = start_date - timedelta(days=start_date.weekday())
    return [(monday + timedelta(days=i)) for i in range(7)]


# ==========================================
# 🗓️ 日程入力画面（週切り替え＋保存済み反映）
# ==========================================
@schedule_bp.route('/schedule')
@login_required
def schedule():
    week_offset = int(request.args.get('week', 0))
    today = date.today()

    # 週の開始日（月曜日）
    start_of_week = today + timedelta(weeks=week_offset)
    dates = get_week_dates(start_of_week)

    # 🔸 過去週判定
    # （今週より前の週なら編集不可）
    is_past_week = start_of_week < get_week_dates(today)[0]

    # 🔹 ログイン中ユーザーの該当週データを取得
    saved_schedules = Schedule.query.filter(
        Schedule.user_id == current_user.id,
        Schedule.date.in_([d.strftime("%Y-%m-%d") for d in dates])
    ).all()

    # 🔹 日付: 時間帯 の辞書
    saved_dict = {s.date: s.time_type for s in saved_schedules}

    return render_template(
        'schedule.html',
        dates=dates,
        week_offset=week_offset,
        saved_dict=saved_dict,
        is_past_week=is_past_week
    )


# ==========================================
# 💾 日程保存API（Flash付き / 通常フォームPOST対応）
# ==========================================
@schedule_bp.route('/schedule/save', methods=['POST'])
@login_required
def save_schedule():

    # ------------------------------
    # 📌 JS が form で渡す hidden input
    #    <input name="payload" value="JSON文字列">
    # ------------------------------
    payload_raw = request.form.get("payload")

    if not payload_raw:
        flash("保存データが受け取れませんでした。", "error")
        return redirect(url_for('schedule.schedule'))

    try:
        data = json.loads(payload_raw)
    except Exception:
        flash("データ解析でエラーが発生しました。", "error")
        return redirect(url_for('schedule.schedule'))

    # どの週から遷移してきたか
    week_offset = int(request.args.get('week', 0))

    change_count = 0

    for item in data:
        selected_date = item["date"]
        slot = item.get("slot", "").strip()

        existing = Schedule.query.filter_by(
            user_id=current_user.id, date=selected_date
        ).first()

        # --------------------------
        # ❌ 未選択 → 削除処理
        # --------------------------
        if slot == "":
            if existing:
                db.session.delete(existing)
                change_count += 1
            continue

        # --------------------------
        # ✏ 更新 or 新規作成
        # --------------------------
        if existing:
            if existing.time_type != slot:
                existing.time_type = slot
                change_count += 1
        else:
            new_row = Schedule(
                user_id=current_user.id,
                date=selected_date,
                time_type=slot
            )
            db.session.add(new_row)
            change_count += 1

    db.session.commit()

    # Flash（ブラウザ通常遷移前提 → 100%表示される）
    if change_count > 0:
        flash("変更を保存しました！", "success")
    else:
        flash("変更はありません。", "info")

    return redirect(url_for('schedule.schedule', week=week_offset))


# ==========================================
# 📆 週間スケジュール表示（自分＋友達）
# ==========================================
@schedule_bp.route('/schedule/weekly')
@login_required
def weekly():
    """自分＋友達のスケジュールを週単位で表示（自分→友達登録順で左から並べる）"""

    week_offset = int(request.args.get('week', 0))
    today = date.today()
    start_of_week = today + timedelta(weeks=week_offset)
    dates = get_week_dates(start_of_week)
    week_strs = [d.strftime("%Y-%m-%d") for d in dates]

    from models.friend import Friend
    friend_records = Friend.query.filter(
        db.or_(
            db.and_(Friend.user_id == current_user.id, Friend.status == 'accepted'),
            db.and_(Friend.friend_id == current_user.id, Friend.status == 'accepted')
        )
    ).order_by(Friend.id.asc()).all()

    friend_ids = [
        fr.friend_id if fr.user_id == current_user.id else fr.user_id
        for fr in friend_records
    ]

    user_order_ids = [current_user.id] + friend_ids

    from models.models import User
    users = User.query.filter(User.id.in_(user_order_ids)).all()
    user_name_by_id = {u.id: u.username for u in users}

    schedules = Schedule.query.filter(
        Schedule.user_id.in_(user_order_ids),
        Schedule.date.in_(week_strs)
    ).all()

    schedule_map = {(s.user_id, s.date): s.time_type for s in schedules}

    data = {}
    for date_str in week_strs:
        row = []
        for uid in user_order_ids:
            slot = schedule_map.get((uid, date_str))
            if slot:
                row.append({
                    'name': user_name_by_id.get(uid, ''),
                    'slot': slot
                })
        data[date_str] = row

    return render_template(
        'weekly.html',
        dates=dates,
        week_offset=week_offset,
        data=data
    )
