import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
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
        <title>JobFit - AI Resume Analyzer</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }
            .container {
                max-width: 700px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            .logo {
                text-align: center;
                margin-bottom: 30px;
            }
            .logo h1 {
                font-size: 42px;
                color: #667eea;
                margin-bottom: 5px;
            }
            .logo p {
                color: #666;
                font-size: 16px;
            }
            label {
                display: block;
                font-weight: 600;
                margin-bottom: 8px;
                color: #333;
            }
            input[type="file"] {
                width: 100%;
                padding: 12px;
                border: 2px dashed #ddd;
                border-radius: 10px;
                margin-bottom: 20px;
                cursor: pointer;
            }
            input[type="file"]:hover {
                border-color: #667eea;
            }
            textarea {
                width: 100%;
                height: 120px;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 10px;
                font-size: 14px;
                resize: vertical;
                margin-bottom: 20px;
            }
            textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                width: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
            }
            .features {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 30px;
                padding-top: 30px;
                border-top: 1px solid #eee;
            }
            .feature {
                text-align: center;
                padding: 10px;
            }
            .feature-icon {
                font-size: 24px;
                margin-bottom: 5px;
            }
            .feature-text {
                font-size: 12px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <h1>JobFit</h1>
                <p>AI-Powered Resume Analyzer</p>
            </div>

            <form action="/analyze" method="post" enctype="multipart/form-data">
                <label>Upload Your Resume</label>
                <input type="file" name="cv_file" accept=".pdf,.docx" required>

                <label>Job Description</label>
                <textarea name="job_description" placeholder="Paste the job description here..." required></textarea>

                <button type="submit">🚀 Analyze My Resume</button>
            </form>

            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-text">Match Score</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">💡</div>
                    <div class="feature-text">Smart Suggestions</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">✅</div>
                    <div class="feature-text">Skill Analysis</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">📝</div>
                    <div class="feature-text">Cover Letter Tips</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(cv_file: UploadFile = File(...), job_description: str = Form(...)):
    suffix = os.path.splitext(cv_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await cv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cv_text = parse_file(tmp_path)
        result = analyze_cv(cv_text, job_description)

        if "error" in result:
            results_html = f"<p style='color: red;'>Error: {result['error']}</p>"
        else:
            score = result.get('match_score', 0)
            score_color = "#28a745" if score >= 70 else "#ffc107" if score >= 50 else "#dc3545"

            results_html = f"""
            <div class="score-card">
                <div class="score-number" style="color: {score_color}">{score}</div>
                <div class="score-label">Match Score</div>
            </div>

            <div class="section">
                <h3>✅ Matching Skills</h3>
                <div class="tags matching">
                    {"".join(f'<span class="tag">{skill}</span>' for skill in result.get('matching_skills', [])) or '<span class="tag">None found</span>'}
                </div>
            </div>

            <div class="section">
                <h3>❌ Missing Skills</h3>
                <div class="tags missing">
                    {"".join(f'<span class="tag">{skill}</span>' for skill in result.get('missing_skills', [])) or '<span class="tag">None</span>'}
                </div>
            </div>

            <div class="section">
                <h3>💡 Improvement Suggestions</h3>
                <ul>
                    {"".join(f"<li>{s}</li>" for s in result.get('suggestions', []))}
                </ul>
            </div>

            <div class="section">
                <h3>📝 Cover Letter Points</h3>
                <ul>
                    {"".join(f"<li>{p}</li>" for p in result.get('cover_letter_points', []))}
                </ul>
            </div>
            """
    finally:
        os.unlink(tmp_path)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>JobFit - Analysis Results</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #667eea;
                margin-bottom: 30px;
                text-align: center;
            }}
            .score-card {{
                text-align: center;
                padding: 30px;
                background: #f8f9fa;
                border-radius: 15px;
                margin-bottom: 30px;
            }}
            .score-number {{
                font-size: 72px;
                font-weight: bold;
            }}
            .score-label {{
                font-size: 18px;
                color: #666;
                margin-top: 5px;
            }}
            .section {{
                margin-bottom: 25px;
            }}
            h3 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 18px;
            }}
            .tags {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .tag {{
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
            }}
            .matching .tag {{
                background: #d4edda;
                color: #155724;
            }}
            .missing .tag {{
                background: #f8d7da;
                color: #721c24;
            }}
            ul {{
                list-style: none;
            }}
            li {{
                padding: 10px 15px;
                background: #f8f9fa;
                margin-bottom: 8px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .back-btn {{
                display: inline-block;
                margin-top: 20px;
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
            }}
            .back-btn:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Analysis Results</h1>
            {results_html}
            <a href="/" class="back-btn">← Analyze Another Resume</a>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)