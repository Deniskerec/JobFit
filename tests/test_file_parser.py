import sys
sys.path.insert(0, "/Users/zetor/Documents/projects/JobFit")

from src.services.file_parser import parse_file
import pytest


def test_parse_pdf():
    result = parse_file("/Users/zetor/Documents/projects/JobFit/uploads/sample.pdf")
    assert result is not None
    assert len(result) > 0


def test_parse_docx():
    result = parse_file("/Users/zetor/Documents/projects/JobFit/uploads/sample.docx")
    assert result is not None
    assert len(result) > 0


def test_unsupported_file():
    with pytest.raises(ValueError):
        parse_file("/Users/zetor/Documents/projects/JobFit/uploads/sample.txt")