import json
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


def save_analysis(job_description, analysis_result):
    """Save CV analysis to Supabase"""
    data = {
        "job_description": job_description,
        "match_score": analysis_result.get("match_score", 0),
        "matching_skills": json.dumps(analysis_result.get("matching_skills", [])),
        "missing_skills": json.dumps(analysis_result.get("missing_skills", [])),
        "suggestions": json.dumps(analysis_result.get("suggestions", [])),
        "cover_letter_points": json.dumps(analysis_result.get("cover_letter_points", []))
    }

    response = supabase.table("cv_analyses").insert(data).execute()
    return response


def get_all_analyses():
    """Get all saved analyses"""
    response = supabase.table("cv_analyses").select("*").execute()
    return response.data


# Test it
if __name__ == "__main__":
    test_result = {
        "match_score": 75,
        "matching_skills": ["Python", "SQL"],
        "missing_skills": ["AWS"],
        "suggestions": ["Add AWS experience"],
        "cover_letter_points": ["Emphasize Python skills"]
    }

    save_analysis("Data Engineer - Python, SQL, AWS required", test_result)
    print("Saved to Supabase!")

    all_data = get_all_analyses()
    print("All analyses:", all_data)