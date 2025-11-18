import os
import tempfile
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.services.file_parser import parse_file
from src.services.ai_analizer import analyze_cv
from src.services.cv_modifier import modify_cv

app = FastAPI(title="JobFit - CV Analyzer")

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Store for temporary files (in production, use proper storage)
temp_storage = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, cv_file: UploadFile = File(...), job_description: str = Form(...)):
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

        if "error" in result:
            return f"<p>Error: {result['error']}</p>"

        # Calculate score color
        score = result.get('match_score', 0)
        if score >= 70:
            score_color = "#28a745"
        elif score >= 50:
            score_color = "#ffc107"
        else:
            score_color = "#dc3545"

        return templates.TemplateResponse("results.html", {
            "request": request,
            "score": score,
            "score_color": score_color,
            "matching_skills": result.get('matching_skills', []),
            "missing_skills": result.get('missing_skills', []),
            "suggestions": result.get('suggestions', []),
            "cover_letter_points": result.get('cover_letter_points', []),
            "cv_text": cv_text,
            "filename": cv_file.filename
        })

    except Exception as e:
        return f"<p>Error: {str(e)}</p>"
    finally:
        os.unlink(tmp_path)


@app.post("/apply-changes", response_class=HTMLResponse)
async def apply_changes(
        request: Request,
        cv_text: str = Form(...),
        filename: str = Form(...),
        suggestions: List[str] = Form(...)
):
    """Show edit page for suggestions"""
    return templates.TemplateResponse("edit_suggestions.html", {
        "request": request,
        "cv_text": cv_text,
        "filename": filename,
        "suggestions": suggestions
    })


@app.post("/process-changes", response_class=HTMLResponse)
async def process_changes(
        request: Request,
        cv_text: str = Form(...),
        filename: str = Form(...),
        suggestions: List[str] = Form(...)
):
    """Actually modify the CV with edited suggestions"""
    try:
        # Filter out empty suggestions
        valid_suggestions = [s.strip() for s in suggestions if s.strip()]

        if not valid_suggestions:
            return "<p>Error: No suggestions provided</p>"

        # Modify CV
        output_path, improved_text = modify_cv(cv_text, valid_suggestions, filename)

        # Store the file path temporarily
        temp_storage[filename] = output_path

        return templates.TemplateResponse("download.html", {
            "request": request,
            "filename": filename,
            "improved_text": improved_text
        })

    except Exception as e:
        return f"<p>Error: {str(e)}</p>"


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download the improved CV"""
    if filename not in temp_storage:
        return {"error": "File not found"}

    file_path = temp_storage[filename]
    return FileResponse(
        path=file_path,
        filename=f"improved_{filename}",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)