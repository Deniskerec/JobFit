import sys

sys.path.insert(0, "/Users/zetor/Documents/projects/JobFit")

import pytest
import os
import tempfile
from src.services.file_parser import parse_file, parse_pdf, parse_docx
from src.services.ai_analizer import analyze_cv, build_prompt
from src.services.cv_modifier import modify_cv, build_modification_prompt
from src.services.storage import sanitize_filename
from src.services.auth import login_user


# ==================== FILE PARSER TESTS ====================

def test_parse_pdf():
    """Test PDF parsing"""
    result = parse_file("/Users/zetor/Documents/projects/JobFit/uploads/sample.pdf")
    assert result is not None
    assert len(result) > 0
    assert isinstance(result, str)
    print("✅ PDF parsing works")


def test_parse_docx():
    """Test DOCX parsing"""
    result = parse_file("/Users/zetor/Documents/projects/JobFit/uploads/sample.docx")
    assert result is not None
    assert len(result) > 0
    assert isinstance(result, str)
    print("✅ DOCX parsing works")


def test_unsupported_file():
    """Test unsupported file type"""
    with pytest.raises(ValueError):
        parse_file("/Users/zetor/Documents/projects/JobFit/uploads/sample.txt")
    print("✅ Correctly rejects unsupported files")


def test_parse_pdf_content():
    """Test that PDF content is extracted"""
    result = parse_pdf("/Users/zetor/Documents/projects/JobFit/uploads/sample.pdf")
    assert len(result) > 20  # Should have some content
    print("✅ PDF content extracted successfully")


def test_parse_docx_content():
    """Test that DOCX content is extracted"""
    result = parse_docx("/Users/zetor/Documents/projects/JobFit/uploads/sample.docx")
    assert len(result) > 20  # Should have some content
    print("✅ DOCX content extracted successfully")


# ==================== AI ANALYZER TESTS ====================

def test_analyze_cv():
    """Test CV analysis with AI"""
    test_cv = """
    JOHN SMITH
    Data Engineer
    Email: john@email.com

    EXPERIENCE:
    - 5 years of Python development
    - SQL database management
    - Built ETL pipelines
    """

    test_job = "Data Engineer - Python, SQL, AWS required. 3+ years experience."

    result = analyze_cv(test_cv, test_job, save_to_db=False)

    assert result is not None
    assert "match_score" in result
    assert "matching_skills" in result
    assert "missing_skills" in result
    assert "suggestions" in result

    assert isinstance(result["match_score"], (int, float))
    assert 0 <= result["match_score"] <= 100

    print(f"✅ AI analysis works - Score: {result['match_score']}")


def test_build_prompt():
    """Test prompt building"""
    cv_text = "Test CV content"
    job_desc = "Test job description"

    prompt = build_prompt(cv_text, job_desc)

    assert cv_text in prompt
    assert job_desc in prompt
    assert "match_score" in prompt.lower()

    print("✅ Prompt building works")


def test_analyze_cv_returns_suggestions():
    """Test that analysis returns suggestions"""
    test_cv = "Junior Developer with 1 year of experience"
    test_job = "Senior Engineer - 5+ years required, AWS, Docker, Kubernetes"

    result = analyze_cv(test_cv, test_job, save_to_db=False)

    assert len(result["suggestions"]) > 0
    assert len(result["missing_skills"]) > 0

    print(f"✅ AI returns {len(result['suggestions'])} suggestions")


def test_analyze_cv_structure():
    """Test that CV analysis returns proper structure"""
    test_cv = "Software Engineer with Python experience"
    test_job = "Python Developer needed"

    result = analyze_cv(test_cv, test_job, save_to_db=False)

    assert isinstance(result["matching_skills"], list)
    assert isinstance(result["missing_skills"], list)
    assert isinstance(result["suggestions"], list)
    assert isinstance(result["cover_letter_points"], list)

    print("✅ AI analysis returns correct structure")


# ==================== CV MODIFIER TESTS ====================

def test_build_modification_prompt():
    """Test prompt building for CV modification"""
    cv_text = "Test CV"
    suggestions = ["Add AWS experience", "Quantify achievements"]

    prompt = build_modification_prompt(cv_text, suggestions)

    assert cv_text in prompt
    assert "AWS experience" in prompt
    assert "Quantify achievements" in prompt

    print("✅ Modification prompt building works")


def test_modify_cv():
    """Test CV modification with AI"""
    test_cv = """
    JOHN SMITH
    Data Engineer

    EXPERIENCE:
    - Built data pipelines
    - Used Python and SQL
    """

    suggestions = ["Add quantified metrics", "Mention cloud technologies"]

    output_path, improved_text = modify_cv(test_cv, suggestions, "test_resume.docx")

    assert output_path is not None
    assert improved_text is not None
    assert len(improved_text) > 0
    assert os.path.exists(output_path)

    # Cleanup
    os.unlink(output_path)

    print("✅ CV modification works")


def test_modify_cv_creates_docx():
    """Test that DOCX file is created"""
    test_cv = "Test CV content with some experience"
    suggestions = ["Add more details"]

    output_path, _ = modify_cv(test_cv, suggestions, "test.docx")

    assert output_path.endswith(".docx")
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

    # Cleanup
    os.unlink(output_path)

    print("✅ DOCX file created successfully")


def test_modify_cv_with_multiple_suggestions():
    """Test CV modification with multiple suggestions"""
    test_cv = "Basic CV content"
    suggestions = [
        "Add technical skills",
        "Include achievements",
        "Add education section"
    ]

    output_path, improved_text = modify_cv(test_cv, suggestions, "multi_test.docx")

    assert len(improved_text) > len(test_cv)  # Should be expanded

    # Cleanup
    os.unlink(output_path)

    print("✅ Multiple suggestions handled correctly")


# ==================== STORAGE TESTS ====================

def test_sanitize_filename():
    """Test filename sanitization"""
    assert sanitize_filename("My Resume.docx") == "My_Resume.docx"
    assert sanitize_filename("CV Señor López.pdf") == "CV_Seor_Lpez.pdf"
    assert sanitize_filename("résumé_2024.docx") == "rsum_2024.docx"

    print("✅ Filename sanitization works")


def test_sanitize_removes_special_chars():
    """Test that special characters are removed"""
    result = sanitize_filename("Test@#$%File.docx")
    assert "@" not in result
    assert "#" not in result
    assert "$" not in result

    print("✅ Special characters removed")


def test_sanitize_preserves_extension():
    """Test that file extension is preserved"""
    result = sanitize_filename("My File.docx")
    assert result.endswith(".docx")

    result = sanitize_filename("Another File.pdf")
    assert result.endswith(".pdf")

    print("✅ File extensions preserved")


def test_sanitize_spaces():
    """Test that spaces are replaced with underscores"""
    result = sanitize_filename("Multi Word File Name.docx")
    assert " " not in result
    assert "_" in result

    print("✅ Spaces replaced with underscores")


# ==================== AUTH TESTS ====================

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    result = login_user("nonexistent@example.com", "wrongpassword")

    assert result["success"] == False

    print("✅ Login correctly rejects invalid credentials")


def test_login_returns_proper_structure():
    """Test that login returns proper structure"""
    result = login_user("test@example.com", "wrong")

    assert "success" in result
    assert isinstance(result["success"], bool)

    print("✅ Login returns correct structure")


# ==================== INTEGRATION TESTS ====================

def test_full_workflow_structure():
    """Test that the full workflow structure works"""
    # 1. Parse CV
    cv_text = """
    JANE DOE
    Software Engineer
    5 years Python experience
    """

    # 2. Analyze
    job_desc = "Python Developer - 3+ years"
    result = analyze_cv(cv_text, job_desc, save_to_db=False)

    # 3. Use suggestions
    suggestions = result["suggestions"][:2]  # Take first 2

    # 4. Modify CV
    output_path, improved = modify_cv(cv_text, suggestions, "workflow_test.docx")

    assert os.path.exists(output_path)
    assert len(improved) > 0

    # Cleanup
    os.unlink(output_path)

    print("✅ Full workflow structure works")


# ==================== EDGE CASES ====================

def test_empty_suggestions():
    """Test CV modification with empty suggestions"""
    test_cv = "Basic CV"
    suggestions = []

    # Should handle gracefully or raise appropriate error
    try:
        output_path, _ = modify_cv(test_cv, suggestions, "empty.docx")
        if os.path.exists(output_path):
            os.unlink(output_path)
        print("✅ Empty suggestions handled")
    except Exception as e:
        print(f"⚠️  Empty suggestions cause error: {str(e)}")


def test_very_long_cv():
    """Test analysis with very long CV"""
    long_cv = "Experience: " + "Python developer " * 200
    job = "Python Developer needed"

    result = analyze_cv(long_cv, job, save_to_db=False)

    assert result is not None
    assert "match_score" in result

    print("✅ Long CV handled correctly")


def test_special_characters_in_cv():
    """Test CV with special characters"""
    cv_with_special = """
    José García
    Email: josé@email.com
    Skills: Python, C++, C#
    """

    job = "Developer needed"
    result = analyze_cv(cv_with_special, job, save_to_db=False)

    assert result is not None

    print("✅ Special characters in CV handled")


# ==================== RUN ALL TESTS ====================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 RUNNING ALL JOBFIT TESTS")
    print("=" * 60 + "\n")

    pytest.main([__file__, "-v", "-s"])