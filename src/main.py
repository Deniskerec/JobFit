import os
import tempfile
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Request, Cookie
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.services.file_parser import parse_file
from src.services.ai_analizer import analyze_cv
from src.services.cv_modifier import modify_cv
from src.services.auth import signup_user, login_user, get_user_from_token
from src.services.storage import upload_file, download_file, get_file_url
from src.services.database import save_analysis, get_user_analyses, get_analysis_by_id, update_analysis_improved_cv
from src.services.cover_letter_generator import generate_cover_letter, create_cover_letter_docx
from src.services.cv_builder import build_cv_from_info, generate_cv_file

app = FastAPI(title="JobFit - CV Analyzer")

# Get the base directory
# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Debug: Print paths
print(f"BASE_DIR: {BASE_DIR}")
print(f"Static dir: {BASE_DIR / 'static'}")
print(f"Static dir exists: {(BASE_DIR / 'static').exists()}")

# Mount static files with error handling
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    print(f"✅ Static files mounted from: {static_dir}")
else:
    print(f"⚠️ WARNING: Static directory not found at {static_dir}")
    # Try alternative path (in case of deployment)
    alt_static_dir = Path("/opt/render/project/src/src/static")
    if alt_static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(alt_static_dir)), name="static")
        print(f"✅ Static files mounted from alternative path: {alt_static_dir}")
    else:
        print(f"❌ Static files not found at alternative path either")

# Setup templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_current_user(access_token: Optional[str]):
    """Get current user from cookie"""
    if not access_token:
        return None
    result = get_user_from_token(access_token)
    if result["success"]:
        return result["user"]
    return None


# ==================== AUTH ROUTES ====================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    result = login_user(email, password)

    if result["success"]:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=result["session"].access_token,
            httponly=True,
            max_age=3600 * 24 * 7  # 7 days
        )
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password"
        })


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "signup_disabled": True
    })


@app.post("/signup", response_class=HTMLResponse)
async def signup(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
):
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "error": "Signups are currently disabled. Please contact the administrator."
    })

    result = signup_user(email, password, name)

 #   if result["success"]:
  #      return templates.TemplateResponse("signup.html", {
   #         "request": request,
    #        "success": "Account created! Please login."
     #   })
   # else:
    #    return templates.TemplateResponse("signup.html", {
     #       "request": request,
      #      "error": f"Failed to create account: {result['error']}"
       # })


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# ==================== MAIN ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, access_token: Optional[str] = Cookie(None)):
    user = get_current_user(access_token)
    if not user:
        # Show landing page if not logged in
        return templates.TemplateResponse("landing.html", {"request": request})
    # Show dashboard if logged in
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request, access_token: Optional[str] = Cookie(None)):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("upload.html", {"request": request, "user": user})


@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request, access_token: Optional[str] = Cookie(None)):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("create.html", {"request": request, "user": user})


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, access_token: Optional[str] = Cookie(None)):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Get user's analyses from database
    analyses = get_user_analyses(user.id)

    return templates.TemplateResponse("history.html", {
        "request": request,
        "user": user,
        "analyses": analyses
    })


@app.get("/analysis/{analysis_id}", response_class=HTMLResponse)
async def analysis_detail(
        analysis_id: int,
        request: Request,
        access_token: Optional[str] = Cookie(None)
):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Get analysis with user verification
    analysis = get_analysis_by_id(analysis_id, user.id)

    if not analysis:
        return "<p>Error: Analysis not found or you don't have permission to view it</p>"

    return templates.TemplateResponse("analysis_detail.html", {
        "request": request,
        "user": user,
        "analysis": analysis
    })


# ==================== CV GENERATION ====================

@app.post("/generate-cv", response_class=HTMLResponse)
async def generate_cv(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        phone: str = Form(...),
        linkedin: str = Form(""),
        summary: str = Form(...),
        job_title_1: str = Form(""),
        company_1: str = Form(""),
        duration_1: str = Form(""),
        responsibilities_1: str = Form(""),
        degree: str = Form(""),
        university: str = Form(""),
        grad_year: str = Form(""),
        skills: str = Form(...),
        job_description: str = Form(""),
        access_token: Optional[str] = Cookie(None)
):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        # Build CV data
        cv_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "summary": summary,
            "experience": [],
            "education": {},
            "skills": skills
        }

        # Only add experience if provided
        if job_title_1 and job_title_1.strip():
            cv_data["experience"].append({
                "title": job_title_1,
                "company": company_1 or "N/A",
                "duration": duration_1 or "N/A",
                "responsibilities": responsibilities_1 or "N/A"
            })

        # Only add education if provided
        if degree and degree.strip():
            cv_data["education"] = {
                "degree": degree,
                "university": university or "N/A",
                "year": grad_year or "N/A"
            }

        # Generate CV text with AI
        cv_text = build_cv_from_info(cv_data)

        # Create DOCX file
        output_path = generate_cv_file(cv_text, f"{name.replace(' ', '_')}_resume.docx")

        # Upload to storage WITH ACCESS TOKEN
        upload_result = upload_file(output_path, f"generated_{name.replace(' ', '_')}_resume.docx", user.id,
                                    access_token)
        original_cv_storage_path = upload_result.get("path") if upload_result["success"] else None

        # Clean up temp file
        os.unlink(output_path)

        # If job description provided, analyze it
        if job_description.strip():
            result = analyze_cv(cv_text, job_description, save_to_db=False)

            # Save analysis
            save_analysis(
                user_id=user.id,
                job_description=job_description,
                analysis_result=result,
                original_cv_path=original_cv_storage_path
            )

            # Calculate score color
            score = result.get('match_score', 0)
            if score >= 70:
                score_color = "#10b981"
            elif score >= 50:
                score_color = "#f59e0b"
            else:
                score_color = "#ef4444"

            return templates.TemplateResponse("results.html", {
                "request": request,
                "score": score,
                "score_color": score_color,
                "matching_skills": result.get('matching_skills', []),
                "missing_skills": result.get('missing_skills', []),
                "suggestions": result.get('suggestions', []),
                "cover_letter_points": result.get('cover_letter_points', []),
                "cv_text": cv_text,
                "filename": f"{name.replace(' ', '_')}_resume.docx",
                "original_cv_path": original_cv_storage_path,
                "user": user
            })
        else:
            # No job description, just download the generated CV
            download_url_result = get_file_url(original_cv_storage_path, access_token)
            download_url = download_url_result.get("url") if download_url_result["success"] else None

            return templates.TemplateResponse("download.html", {
                "request": request,
                "filename": f"{name.replace(' ', '_')}_resume.docx",
                "improved_text": cv_text,
                "download_url": download_url,
                "user": user
            })

    except Exception as e:
        print(f"Generate CV error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"<p>Error: {str(e)}</p>"

# ==================== CV ANALYSIS ====================

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
        request: Request,
        cv_file: UploadFile = File(...),
        job_description: str = Form(...),
        access_token: Optional[str] = Cookie(None)
):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    suffix = os.path.splitext(cv_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await cv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Upload with access token
        upload_result = upload_file(tmp_path, f"original_{cv_file.filename}", user.id, access_token)
        original_cv_storage_path = upload_result.get("path") if upload_result["success"] else None

        # Parse and analyze
        cv_text = parse_file(tmp_path)
        result = analyze_cv(cv_text, job_description, save_to_db=False)

        if "error" in result:
            return f"<p>Error: {result['error']}</p>"

        # Save to database
        save_analysis(
            user_id=user.id,
            job_description=job_description,
            analysis_result=result,
            original_cv_path=original_cv_storage_path
        )

        # Calculate score color
        score = result.get('match_score', 0)
        if score >= 70:
            score_color = "#10b981"
        elif score >= 50:
            score_color = "#f59e0b"
        else:
            score_color = "#ef4444"

        return templates.TemplateResponse("results.html", {
            "request": request,
            "score": score,
            "score_color": score_color,
            "matching_skills": result.get('matching_skills', []),
            "missing_skills": result.get('missing_skills', []),
            "suggestions": result.get('suggestions', []),
            "cover_letter_points": result.get('cover_letter_points', []),
            "cv_text": cv_text,
            "filename": cv_file.filename,
            "original_cv_path": original_cv_storage_path,
            "user": user
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
        original_cv_path: str = Form(...),
        suggestions: List[str] = Form(...),
        access_token: Optional[str] = Cookie(None)
):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("edit_suggestions.html", {
        "request": request,
        "cv_text": cv_text,
        "filename": filename,
        "original_cv_path": original_cv_path,
        "suggestions": suggestions,
        "user": user
    })


@app.post("/process-changes", response_class=HTMLResponse)
async def process_changes(
        request: Request,
        cv_text: str = Form(...),
        filename: str = Form(...),
        original_cv_path: str = Form(...),
        suggestions: List[str] = Form(...),
        access_token: Optional[str] = Cookie(None)
):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        valid_suggestions = [s.strip() for s in suggestions if s.strip()]

        if not valid_suggestions:
            return "<p>Error: No suggestions provided</p>"

        # Modify CV
        output_path, improved_text = modify_cv(cv_text, valid_suggestions, filename)

        # Upload to storage WITH ACCESS TOKEN
        improved_filename = f"improved_{filename}"
        upload_result = upload_file(output_path, improved_filename, user.id, access_token)

        if not upload_result["success"]:
            print(f"Upload failed: {upload_result.get('error')}")
            return f"<p>Error uploading file: {upload_result.get('error')}</p>"

        improved_cv_storage_path = upload_result.get("path")

        # Get download URL WITH ACCESS TOKEN
        url_result = get_file_url(improved_cv_storage_path, access_token)

        if not url_result["success"]:
            print(f"Get URL failed: {url_result.get('error')}")
            return f"<p>Error getting download URL: {url_result.get('error')}</p>"

        download_url = url_result.get("url")

        print(f"Download URL: {download_url}")  # Debug

        # UPDATE: Save improved CV path to the most recent analysis
        analyses = get_user_analyses(user.id)
        if analyses and len(analyses) > 0:
            latest_analysis_id = analyses[0]["id"]
            update_analysis_improved_cv(latest_analysis_id, improved_cv_storage_path)

        # Clean up
        os.unlink(output_path)

        return templates.TemplateResponse("download.html", {
            "request": request,
            "filename": improved_filename,
            "improved_text": improved_text,
            "download_url": download_url,
            "user": user
        })

    except Exception as e:
        print(f"Process changes error: {str(e)}")
        return f"<p>Error: {str(e)}</p>"


# ==================== FILE DOWNLOAD ====================

@app.get("/download-file/{path:path}")
async def download_stored_file(path: str, access_token: Optional[str] = Cookie(None)):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        # Download from Supabase storage WITH ACCESS TOKEN
        temp_path = f"/tmp/{path.split('/')[-1]}"
        result = download_file(path, temp_path, access_token)

        if result["success"]:
            return FileResponse(
                path=temp_path,
                filename=path.split('/')[-1],
                media_type="application/octet-stream"
            )
        else:
            return {"error": "File not found"}
    except Exception as e:
        return {"error": str(e)}
# ==================== COVER LETTER ====================

@app.get("/cover-letter", response_class=HTMLResponse)
async def cover_letter_page(request: Request, access_token: Optional[str] = Cookie(None)):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("cover_letter.html", {"request": request, "user": user})


@app.post("/generate-cover-letter", response_class=HTMLResponse)
async def generate_cover_letter_route(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        phone: str = Form(""),
        linkedin: str = Form(""),
        resume_file: Optional[UploadFile] = File(None),
        resume_text: str = Form(""),
        job_title: str = Form(...),
        company_name: str = Form(...),
        job_description: str = Form(...),
        access_token: Optional[str] = Cookie(None)
):
    user = get_current_user(access_token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    tmp_path = None
    output_path = None

    try:
        # Get resume text
        if resume_file and resume_file.filename:
            suffix = os.path.splitext(resume_file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await resume_file.read()
                tmp.write(content)
                tmp_path = tmp.name

            resume_content = parse_file(tmp_path)
        elif resume_text.strip():
            resume_content = resume_text
        else:
            return "<p>Error: Please upload a resume or paste resume text</p>"

        user_info = {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin
        }

        # Generate cover letter with AI
        cover_letter_text = generate_cover_letter(resume_content, job_description, user_info)

        # Create DOCX file
        filename = f"{name.replace(' ', '_')}_cover_letter_{company_name.replace(' ', '_')}.docx"
        output_path = create_cover_letter_docx(cover_letter_text, user_info, filename)

        print(f"Created cover letter at: {output_path}")

        # Upload to storage
        upload_result = upload_file(output_path, filename, user.id, access_token)
        print(f"Upload result: {upload_result}")

        storage_path = upload_result.get("path") if upload_result["success"] else None

        # Get download URL
        download_url = None
        if storage_path:
            print(f"Storage path: {storage_path}")
            url_result = get_file_url(storage_path, access_token)
            print(f"URL result: {url_result}")
            download_url = url_result.get("url") if url_result["success"] else None
            print(f"Download URL: {download_url}")

        if not download_url:
            print("ERROR: No download URL generated!")
            return "<p>Error: Could not generate download URL. Check logs.</p>"

        return templates.TemplateResponse("cover_letter_preview.html", {
            "request": request,
            "user": user,
            "cover_letter_text": cover_letter_text,
            "download_url": download_url,
            "job_title": job_title,
            "company_name": company_name,
            "filename": filename
        })

    except Exception as e:
        print(f"Cover letter generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"<p>Error: {str(e)}</p>"

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass

        if output_path and os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except:
                pass

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)