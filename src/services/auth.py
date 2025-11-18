import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


def signup_user(email, password, name):
    """Create a new user account"""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "name": name
                }
            }
        })
        return {"success": True, "user": response.user}
    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(email, password):
    """Login user and get session"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return {"success": True, "session": response.session, "user": response.user}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_from_token(access_token):
    """Get user info from access token"""
    try:
        response = supabase.auth.get_user(access_token)
        return {"success": True, "user": response.user}
    except Exception as e:
        return {"success": False, "error": str(e)}


def logout_user(access_token):
    """Logout user"""
    try:
        supabase.auth.sign_out()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}