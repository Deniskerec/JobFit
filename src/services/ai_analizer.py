import json
from openai import OpenAI
from dotenv import load_dotenv
from src.services.file_parser import parse_file
from src.services.database import save_analysis

load_dotenv()
client = OpenAI()


def build_prompt(cv_text, job_description):
    """Build the prompt to send to OpenAI"""
    prompt = f"""
You are a professional CV/Resume analyzer. Analyze how well this CV matches the job description.

JOB DESCRIPTION:
{job_description}

CV/RESUME:
{cv_text}

Analyze the CV and return a JSON response with this exact structure:
{{
    "match_score": <number from 0-100>,
    "matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "suggestions": [
        "suggestion 1",
        "suggestion 2",
        "suggestion 3"
    ],
    "cover_letter_points": [
        "point to emphasize 1",
        "point to emphasize 2"
    ]
}}

Return ONLY valid JSON, no other text.
"""
    return prompt


def call_openai(prompt):
    """Send prompt to OpenAI and get response"""
    response = client.responses.create(
        model="gpt-5-nano-2025-08-07",
        input=prompt
    )
    return response.output_text


def parse_response(response_text):
    """Parse the JSON response from OpenAI"""
    try:
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response", "raw": response_text}


def analyze_cv(cv_text, job_description, save_to_db=True):
    """Main function: analyze CV against job description"""
    prompt = build_prompt(cv_text, job_description)
    response = call_openai(prompt)
    result = parse_response(response)

    # Save to database if requested
    if save_to_db and "error" not in result:
        save_analysis(job_description, result)
        print("✅ Analysis saved to Supabase!")

    return result


# Test with actual file AND save to database
if __name__ == "__main__":
    cv_path = "/Users/zetor/Documents/projects/JobFit/uploads/sample.pdf"
    cv_text = parse_file(cv_path)

    job_description = "Data Engineer - Python, SQL, AWS experience required. Build and maintain ETL pipelines, work with large datasets, 3+ years experience."

    result = analyze_cv(cv_text, job_description)
    print(json.dumps(result, indent=2))