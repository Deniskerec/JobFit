import os
import re
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


def sanitize_filename(filename):
    """Remove spaces and special characters from filename"""
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return filename


def get_supabase_client(access_token=None):
    """Get Supabase client with optional user token"""
    if access_token:
        # Create client and set the auth token
        client = create_client(url, key)
        client.auth.set_session(access_token, "")  # Set user's token
        return client
    else:
        # Use anon key
        return create_client(url, key)


def upload_file(file_path, file_name, user_id, access_token=None):
    """Upload file to Supabase Storage"""
    try:
        supabase = get_supabase_client(access_token)

        clean_filename = sanitize_filename(file_name)
        storage_path = f"{user_id}/{clean_filename}"

        with open(file_path, 'rb') as f:
            file_data = f.read()

        supabase.storage.from_("cv-files").upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "upsert": "true"
            }
        )

        return {"success": True, "path": storage_path}
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return {"success": False, "error": str(e)}


def download_file(storage_path, local_path, access_token=None):
    """Download file from Supabase Storage"""
    try:
        supabase = get_supabase_client(access_token)
        data = supabase.storage.from_("cv-files").download(storage_path)

        with open(local_path, 'wb') as f:
            f.write(data)

        return {"success": True, "path": local_path}
    except Exception as e:
        print(f"Download error: {str(e)}")
        return {"success": False, "error": str(e)}


def get_file_url(storage_path, access_token=None):
    """Get signed URL for file download"""
    try:
        supabase = get_supabase_client(access_token)

        response = supabase.storage.from_("cv-files").create_signed_url(
            path=storage_path,
            expires_in=3600
        )

        if isinstance(response, dict) and 'signedURL' in response:
            return {"success": True, "url": response['signedURL']}
        else:
            print(f"Unexpected response format: {response}")
            return {"success": False, "error": f"Invalid response: {response}"}
    except Exception as e:
        print(f"Get URL error: {str(e)}")
        return {"success": False, "error": str(e)}


def delete_file(storage_path, access_token=None):
    """Delete file from Supabase Storage"""
    try:
        supabase = get_supabase_client(access_token)
        supabase.storage.from_("cv-files").remove([storage_path])
        return {"success": True}
    except Exception as e:
        print(f"Delete error: {str(e)}")
        return {"success": False, "error": str(e)}