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
    if response.data and len(response.data) > 0:
        analysis = response.data[0]
        # Parse JSON strings back to lists
        analysis["matching_skills"] = json.loads(analysis.get("matching_skills", "[]"))
        analysis["missing_skills"] = json.loads(analysis.get("missing_skills", "[]"))
        analysis["suggestions"] = json.loads(analysis.get("suggestions", "[]"))
        analysis["cover_letter_points"] = json.loads(analysis.get("cover_letter_points", "[]"))
        return analysis
    return None


def get_all_analyses():
    """Get all saved analyses (for testing)"""
    response = supabase.table("cv_analyses").select("*").execute()
    return response.data

def update_analysis_improved_cv(analysis_id, improved_cv_path):
    """Update analysis with improved CV path"""
    try:
        supabase.table("cv_analyses").update({
            "improved_cv_path": improved_cv_path
        }).eq("id", analysis_id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error updating analysis: {str(e)}")
        return {"success": False, "error": str(e)}