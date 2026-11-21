import pdfplumber

def extract_text_from_pdf(path):
    """Extract plain text from a PDF using pdfplumber.
    Returns the concatenated text of all pages.
    """
    with pdfplumber.open(path) as pdf:
        pages = [page.extract_text() or '' for page in pdf.pages]
    return '\n'.join(pages)
