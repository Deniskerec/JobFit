from PyPDF2 import PdfReader
from docx import Document


def parse_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def parse_docx(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text


def parse_file(file_path):
    """Detect file type and parse accordingly"""
    if file_path.endswith(".pdf"):
        return parse_pdf(file_path)
    elif file_path.endswith(".docx"):
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")


# Test it
pdf_path = "/Users/zetor/Documents/projects/JobFit/uploads/sample.docx"
text = parse_file(pdf_path)
print(text)