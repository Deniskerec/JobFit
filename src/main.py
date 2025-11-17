import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import tempfile
import os

from src.services.file_parser import parse_file
from src.services.ai_analizer import analyze_cv

app = FastAPI(title="JobFit - CV Analyzer")


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JobFit - CV Analyzer</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            textarea { width: 100%; height: 100px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; margin-top: 10px; }
            button:hover { background: #0056b3; }
            .result { background: #f4f4f4; padding: 20px; margin-top: 20px; border-radius: 5px; }
            .score { font-size: 24px; font-weight: bold; color: #28a745; }
            .missing { color: #dc3545; }
            .matching { color: #28a745; }
            h3 { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>JobFit - CV Analyzer</h1>
        <form action="/analyze" method="post" enctype="multipart/form-data">
            <label><strong>Upload your CV (PDF or DOCX):</strong></label><br>
            <input type="file" name="cv_file" accept=".pdf,.docx" required><br><br>

            <label><strong>Job Description:</strong></label><br>
            <textarea name="job_description" placeholder="Paste the job description here..." required></textarea><br>

            <button type="submit">Analyze My CV</button>
        </form>
    </body>
    </html>
    """


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(cv_file: UploadFile = File(...), job_description: str = Form(...)):
    # Save uploaded file temporarily
    suffix = os.path.splitext(cv_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await cv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Parse the CV
        cv_text = parse_file(tmp_path)

        # Analyze with AI
        result = analyze_cv(cv_text, job_description)

        # Build results HTML
        if "error" in result:
            results_html = f"<p>Error: {result['error']}</p>"
        else:
            results_html = f"""
            <div class="result">
                <p class="score">Match Score: {result.get('match_score', 0)}/100</p>

                <h3>✅ Matching Skills:</h3>
                <ul class="matching">
                    {"".join(f"<li>{skill}</li>" for skill in result.get('matching_skills', []))}
                </ul>

                <h3>❌ Missing Skills:</h3>
                <ul class="missing">
                    {"".join(f"<li>{skill}</li>" for skill in result.get('missing_skills', []))}
                </ul>

                <h3>💡 Suggestions:</h3>
                <ul>
                    {"".join(f"<li>{s}</li>" for s in result.get('suggestions', []))}
                </ul>

                <h3>📝 Cover Letter Points:</h3>
                <ul>
                    {"".join(f"<li>{p}</li>" for p in result.get('cover_letter_points', []))}
                </ul>
            </div>
            """
    finally:
        os.unlink(tmp_path)  # Clean up temp file

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>JobFit - Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
            .result {{ background: #f4f4f4; padding: 20px; margin-top: 20px; border-radius: 5px; }}
            .score {{ font-size: 24px; font-weight: bold; color: #28a745; }}
            .missing {{ color: #dc3545; }}
            .matching {{ color: #28a745; }}
            h3 {{ margin-top: 20px; }}
            a {{ color: #007bff; }}
        </style>
    </head>
    <body>
        <h1>Analysis Results</h1>
        {results_html}
        <br>
        <a href="/">← Analyze Another CV</a>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)