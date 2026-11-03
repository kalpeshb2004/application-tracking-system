import re

import pdfplumber

MAX_BYTES = 2 * 1024 * 1024     # 2 MB
MAX_PAGES = 6
MAX_CHARS = 30_000
MIN_CHARS = 100


class ResumeError(Exception):
    """The message is safe to show to the user."""


def extract_pdf_text(uploaded_file):
    # 1. Size first, so a huge file is rejected before any work
    if uploaded_file.size > MAX_BYTES:
        raise ResumeError("File is too large. Max 2 MB.")

    # 2. Check real file content, not the name or the browser's content type
    head = uploaded_file.read(5)
    uploaded_file.seek(0)
    if head != b"%PDF-":
        raise ResumeError("Only PDF files are supported.")

    # 3. Read text. Never show parser internals to the user
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            if len(pdf.pages) > MAX_PAGES:
                raise ResumeError(f"Resume has too many pages. Max {MAX_PAGES}.")
            pages = [page.extract_text() or "" for page in pdf.pages]
    except ResumeError:
        raise
    except Exception:
        raise ResumeError("Could not read this PDF. It may be damaged or password protected.")

    # 4. Clean up
    text = "\n".join(pages).replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if len(text) < MIN_CHARS:
        raise ResumeError("No readable text found. Scanned or image-only PDFs are not supported.")
    return text[:MAX_CHARS]