"""
Module for handling Word document operations.
"""
import docx

def read_docx(file_path: str) -> str:
    """Read a Word document and return its text content."""
    try:
        doc = docx.Document(file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        raise Exception(f"Error reading Word document: {str(e)}")

if __name__ == "__main__":
    try:
        content = read_docx("Pseudo code- watchbill model.docx")
        print(content)
    except Exception as e:
        print(f"Error: {str(e)}") 