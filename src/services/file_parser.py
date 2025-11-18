from docx import Document
import PyPDF2


def parse_docx(file_path):
    """Extract text from DOCX file"""
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


def parse_pdf(file_path):
    """Extract text from PDF file"""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text


def parse_file(file_path):
    """Detect file type and parse accordingly"""
    if file_path.endswith('.pdf'):
        return parse_pdf(file_path)
    elif file_path.endswith('.docx'):
        return parse_docx(file_path)
    else:
        raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")


# REMOVE OR COMMENT OUT EVERYTHING BELOW THIS LINE:
# if __name__ == "__main__":
#     pdf_path = "/Users/zetor/Documents/projects/JobFit/uploads/sample.pdf"
#     text = parse_file(pdf_path)
#     print(text)