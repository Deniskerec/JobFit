import json
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


def save_analysis(user_id, job_description, analysis_result, original_cv_path=None, improved_cv_path=None):
    """Save CV analysis to Supabase with file paths"""
    data = {
        "user_id": user_id,
        "job_description": job_description,
        "match_score": analysis_result.get("match_score", 0),
        "matching_skills": json.dumps(analysis_result.get("matching_skills", [])),
        "missing_skills": json.dumps(analysis_result.get("missing_skills", [])),
        "suggestions": json.dumps(analysis_result.get("suggestions", [])),
        "cover_letter_points": json.dumps(analysis_result.get("cover_letter_points", [])),
        "original_cv_path": original_cv_path,
        "improved_cv_path": improved_cv_path
    }

    response = supabase.table("cv_analyses").insert(data).execute()
    return response


def get_user_analyses(user_id):
    """Get all analyses for a specific user"""
    response = supabase.table("cv_analyses").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data


def get_analysis_by_id(analysis_id, user_id):
    """Get specific analysis by ID (with user verification)"""
    response = supabase.table("cv_analyses").select("*").eq("id", analysis_id).eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]
    return None


def get_all_analyses():
    """Get all saved analyses (for testing)"""
    response = supabase.table("cv_analyses").select("*").execute()
    return response.data