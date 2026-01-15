from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from app import db, bcrypt
from app.models import User, Profile
from flask_jwt_extended import create_access_token, create_refresh_token
from authlib.integrations.flask_client import OAuth
import os
import secrets

bp = Blueprint('oauth', __name__, url_prefix='/api/auth/oauth')

# Initialize OAuth
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with app context"""
    oauth.init_app(app)
    
    # Register Google OAuth
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    # Register Facebook OAuth
    oauth.register(
        name='facebook',
        client_id=os.getenv('FACEBOOK_CLIENT_ID'),
        client_secret=os.getenv('FACEBOOK_CLIENT_SECRET'),
        access_token_url='https://graph.facebook.com/oauth/access_token',
        authorize_url='https://www.facebook.com/dialog/oauth',
        api_base_url='https://graph.facebook.com/',
        client_kwargs={'scope': 'email public_profile'}
    )


@bp.route('/google', methods=['GET'])
def google_login():
    """Initiate Google OAuth flow"""
    try:
        redirect_uri = os.getenv('OAUTH_REDIRECT_URI') + '/google'
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Google OAuth not configured: {str(e)}'
        }), 500


@bp.route('/facebook', methods=['GET'])
def facebook_login():
    """Initiate Facebook OAuth flow"""
    try:
        redirect_uri = os.getenv('OAUTH_REDIRECT_URI') + '/facebook'
        return oauth.facebook.authorize_redirect(redirect_uri)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Facebook OAuth not configured: {str(e)}'
        }), 500


@bp.route('/callback/google', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        print("=== Google OAuth Callback Started ===")
        token = oauth.google.authorize_access_token()
        print(f"Token received: {token is not None}")
        
        user_info = token.get('userinfo')
        print(f"User info: {user_info}")
        
        if not user_info:
            print("ERROR: No user info in token")
            return redirect(f"{os.getenv('CORS_ORIGINS').split(',')[0]}/login?error=oauth_failed")
        
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        print(f"Email: {email}, Name: {name}")
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        print(f"User exists: {user is not None}")
        
        if not user:
            # Create new user
            print("Creating new user...")
            # Generate a random password (won't be used for OAuth users)
            random_password = secrets.token_urlsafe(32)
            password_hash = bcrypt.generate_password_hash(random_password).decode('utf-8')
            
            user = User(
                email=email,
                fullname=name,
                password_hash=password_hash,
                role='user'
            )
            db.session.add(user)
            db.session.flush()
            
            # Create profile
            profile = Profile(
                user_id=user.id,
                profile_photo=picture if picture else None
            )
            db.session.add(profile)
            db.session.commit()
            print(f"New user created with ID: {user.id}")
        
        # Create tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        print(f"Tokens created")
        
        # Redirect to frontend with tokens
        frontend_url = os.getenv('CORS_ORIGINS').split(',')[0]
        redirect_url = f"{frontend_url}/oauth-callback?access_token={access_token}&refresh_token={refresh_token}&user={user.email}"
        print(f"Redirecting to: {redirect_url}")
        return redirect(redirect_url)
        
    except Exception as e:
        print(f"ERROR in Google OAuth callback: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect(f"{os.getenv('CORS_ORIGINS').split(',')[0]}/login?error=oauth_failed")


@bp.route('/callback/facebook', methods=['GET'])
def facebook_callback():
    """Handle Facebook OAuth callback"""
    try:
        token = oauth.facebook.authorize_access_token()
        
        # Get user info from Facebook
        resp = oauth.facebook.get('me?fields=id,name,email,picture')
        user_info = resp.json()
        
        if not user_info or not user_info.get('email'):
            return redirect(f"{os.getenv('CORS_ORIGINS').split(',')[0]}/login?error=oauth_failed")
        
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', {}).get('data', {}).get('url', '')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            # Generate a random password (won't be used for OAuth users)
            random_password = secrets.token_urlsafe(32)
            password_hash = bcrypt.generate_password_hash(random_password).decode('utf-8')
            
            user = User(
                email=email,
                fullname=name,
                password_hash=password_hash,
                role='user'
            )
            db.session.add(user)
            db.session.flush()
            
            # Create profile
            profile = Profile(
                user_id=user.id,
                profile_photo=picture if picture else None
            )
            db.session.add(profile)
            db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # Redirect to frontend with tokens
        frontend_url = os.getenv('CORS_ORIGINS').split(',')[0]
        return redirect(f"{frontend_url}/oauth-callback?access_token={access_token}&refresh_token={refresh_token}&user={user.email}")
        
    except Exception as e:
        return redirect(f"{os.getenv('CORS_ORIGINS').split(',')[0]}/login?error=oauth_failed")
