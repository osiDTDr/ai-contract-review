from typing import List, Dict
from .vector_store import VectorStore

class KnowledgeBase:
    def __init__(self):
        self.vector_store = VectorStore()
        self._initialize_knowledge()
    
    def _initialize_knowledge(self):
        """初始化法律知识库"""
        legal_knowledge = [
            {
                "content": "合同法第八条：依法成立的合同，对当事人具有法律约束力。当事人应当按照约定履行自己的义务，不得擅自变更或者解除合同。",
                "type": "法律条文",
                "category": "合同效力"
            },
            {
                "content": "合同应当包含以下基本要素：当事人的姓名或者名称和住所；标的；数量；质量；价款或者报酬；履行期限、地点和方式；违约责任；解决争议的方法。",
                "type": "合同要素",
                "category": "合同结构"
            },
            {
                "content": "违约金条款应当合理，不得过分高于造成的损失。违约金过高的，当事人可以请求人民法院或者仲裁机构予以适当减少。",
                "type": "风险提示",
                "category": "违约责任"
            },
            {
                "content": "单方解除权的行使应当符合法定条件，不得滥用。合同中约定的单方解除条件应当明确、合理。",
                "type": "风险提示", 
                "category": "合同解除"
            },
            {
                "content": "争议解决条款应当明确约定解决争议的方式，可以选择协商、调解、仲裁或诉讼。仲裁条款应当明确仲裁机构和仲裁规则。",
                "type": "合同条款",
                "category": "争议解决"
            }
        ]
        
        texts = [item["content"] for item in legal_knowledge]
        metadatas = [{k: v for k, v in item.items() if k != "content"} for item in legal_knowledge]
        
        self.vector_store.add_documents(texts, metadatas)
    
    def search_relevant_knowledge(self, query: str, category: str = None) -> List[Dict]:
        """搜索相关法律知识"""
        results = self.vector_store.similarity_search(query, k=3)
        
        # 如果指定了类别，过滤结果
        if category:
            results = [r for r in results if r["metadata"].get("category") == category]
        
        return results
    
    def get_compliance_guidance(self, text: str) -> List[str]:
        """获取合规指导"""
        guidance = []
        
        # 搜索合同结构相关知识
        structure_results = self.search_relevant_knowledge(text, "合同结构")
        for result in structure_results:
            if result["score"] > 0.7:
                guidance.append(f"参考: {result['content']}")
        
        return guidance
    
    def get_risk_analysis(self, text: str) -> List[Dict]:
        """获取风险分析"""
        risk_analysis = []
        
        # 搜索风险提示
        risk_results = self.search_relevant_knowledge(text, "风险提示")
        for result in risk_results:
            if result["score"] > 0.6:
                risk_analysis.append({
                    "guidance": result["content"],
                    "category": result["metadata"]["category"],
                    "relevance": result["score"]
                })


        return risk_analysis