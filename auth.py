import os
import json
import requests
from flask import Flask, redirect, url_for, session, request, jsonify
from datetime import datetime
from db import get_session
from models import User

class GoogleAuth:
    def __init__(self, app):
        self.app = app
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup authentication routes"""
        
        @self.app.route('/login')
        def login():
            """Redirect to Google OAuth consent screen"""
            redirect_uri = url_for('authorized', _external=True)
            auth_url = (
                f"https://accounts.google.com/o/oauth2/auth?"
                f"client_id={self.client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"scope=openid email profile&"
                f"response_type=code&"
                f"access_type=offline"
            )
            return redirect(auth_url)
        
        @self.app.route('/logout')
        def logout():
            """Logout user and clear session"""
            session.pop('google_token', None)
            session.pop('user_id', None)
            session.pop('user_email', None)
            session.pop('user_name', None)
            return redirect(url_for('index'))
        
        @self.app.route('/login/authorized')
        def authorized():
            """Handle OAuth callback from Google"""
            code = request.args.get('code')
            if not code:
                return 'Access denied: no authorization code received'
            
            try:
                # Exchange code for access token
                token_response = self.exchange_code_for_token(code)
                if not token_response:
                    return 'Failed to exchange code for access token'
                
                # Get user info
                userinfo = self.get_user_info(token_response['access_token'])
                if not userinfo:
                    return 'Failed to fetch user info'
                
                # Create or update user and store basic info in session
                user_data = self.create_or_update_user(userinfo)
                
                # Store user info in session (not the database object)
                session['user_id'] = user_data['id']
                session['user_email'] = user_data['email']
                session['user_name'] = user_data['first_name']
                session['google_token'] = token_response['access_token']
                
                return redirect(url_for('index'))
                
            except Exception as e:
                return f'Authentication error: {str(e)}'
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        redirect_uri = url_for('authorized', _external=True)
        
        token_url = "https://accounts.google.com/o/oauth2/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_user_info(self, access_token):
        """Get user information from Google"""
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(userinfo_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    
    def create_or_update_user(self, google_data):
        """Create or update user in database"""
        session_db = get_session()
        try:
            # Check if user exists
            user = session_db.query(User).filter_by(google_id=google_data['id']).first()
            
            if user:
                # Update existing user
                user.email = google_data['email']
                user.first_name = google_data.get('given_name', '')
                user.last_name = google_data.get('family_name', '')
                user.profile_pic = google_data.get('picture', '')
                
                # Return user data as dictionary (not the database object)
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_pic': user.profile_pic
                }
            else:
                # Create new user
                user = User(
                    google_id=google_data['id'],
                    email=google_data['email'],
                    first_name=google_data.get('given_name', ''),
                    last_name=google_data.get('family_name', ''),
                    profile_pic=google_data.get('picture', ''),
                    created_at=datetime.utcnow()
                )
                session_db.add(user)
                session_db.flush()  # Get the ID without committing
                
                # Return user data as dictionary
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_pic': user.profile_pic
                }
            
            session_db.commit()
            return user_data
        except Exception as e:
            session_db.rollback()
            raise e
        finally:
            session_db.close()
    
    def get_current_user(self):
        """Get current logged in user"""
        user_id = session.get('user_id')
        if not user_id:
            return None
        
        session_db = get_session()
        try:
            user = session_db.query(User).filter_by(id=user_id).first()
            return user
        finally:
            session_db.close()
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return session.get('user_id') is not None
