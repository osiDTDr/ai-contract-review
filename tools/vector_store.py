import faiss
import numpy as np
from typing import List, Dict
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pickle
import os
from config import settings

class VectorStore:
    def __init__(self):
        self.embeddings = self._create_embeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50
        )
        self.index = None
        self.documents = []
        self.metadata = []
    
    def _create_embeddings(self):
        """根据配置创建嵌入模型"""
        if settings.embedding_provider == "openai":
            return OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url
            )
        elif settings.embedding_provider == "ollama":
            return OllamaEmbeddings(
                model=settings.ollama_embedding_model,
                base_url=settings.ollama_base_url
            )
        else:
            raise ValueError(f"不支持的嵌入模型提供商: {settings.embedding_provider}")
        
    def add_documents(self, texts: List[str], metadatas: List[Dict] = None):
        """添加文档到向量库"""
        chunks = []
        chunk_metadata = []
        
        for i, text in enumerate(texts):
            text_chunks = self.text_splitter.split_text(text)
            chunks.extend(text_chunks)
            
            # 为每个chunk添加metadata
            for chunk in text_chunks:
                meta = metadatas[i] if metadatas else {"source": f"doc_{i}"}
                chunk_metadata.append(meta)
        
        # 生成embeddings
        embeddings = self.embeddings.embed_documents(chunks)
        embeddings_array = np.array(embeddings).astype('float32')
        
        # 创建或更新FAISS索引
        if self.index is None:
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
        
        self.index.add(embeddings_array)
        self.documents.extend(chunks)
        self.metadata.extend(chunk_metadata)
    
    def similarity_search(self, query: str, k: int = 3) -> List[Dict]:
        """相似性搜索"""
        if self.index is None:
            return []
        
        query_embedding = self.embeddings.embed_query(query)
        query_array = np.array([query_embedding]).astype('float32')
        
        scores, indices = self.index.search(query_array, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append({
                    "content": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "score": float(scores[0][i])
                })
        
        return results
    
    def save(self, path: str):
        """保存向量库"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(self.index, f"{path}.faiss")
        with open(f"{path}.pkl", "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata
            }, f)
    
    def load(self, path: str):
        """加载向量库"""
        if os.path.exists(f"{path}.faiss"):
            self.index = faiss.read_index(f"{path}.faiss")
            with open(f"{path}.pkl", "rb") as f:
                data = pickle.load(f)
                self.documents = data["documents"]
                self.metadata = data["metadata"]