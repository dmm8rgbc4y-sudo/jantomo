from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.friend import Friend

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    """
    プロフィール情報を表示（読み取り専用）
    """
    friend_count = len(Friend.get_friend_ids(current_user.id))
    created_at_str = current_user.created_at.strftime('%Y-%m-%d')

    return render_template(
        'profile.html',
        username=current_user.username,
        created_at=created_at_str,
        friend_count=friend_count
    )
