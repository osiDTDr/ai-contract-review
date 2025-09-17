import PyPDF2
from docx import Document
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentParser:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def parse_pdf(self, file_path: str) -> str:
        """解析PDF文件"""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    
    def parse_docx(self, file_path: str) -> str:
        """解析Word文档"""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def parse_txt(self, file_path: str) -> str:
        """解析文本文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def split_text(self, text: str) -> List[str]:
        """文本分块"""
        return self.text_splitter.split_text(text)