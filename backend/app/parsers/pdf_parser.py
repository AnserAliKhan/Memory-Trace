import fitz
class PDFParser:
    def parse(self,file_path:str):
        doc=fitz.open(file_path)
        return ''.join(page.get_text() for page in doc)
