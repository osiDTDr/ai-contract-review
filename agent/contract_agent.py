from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from tools.document_parser import DocumentParser
from tools.compliance_checker import ComplianceChecker
from tools.llm_client import LLMClient

class ContractState(TypedDict):
    text: str
    summary: str
    risks: List[Dict]
    compliance: List[str]
    score: int

class ContractReviewAgent:
    def __init__(self):
        self.parser = DocumentParser()
        self.checker = ComplianceChecker()
        self.llm_client = LLMClient()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建LangGraph工作流"""
        workflow = StateGraph(ContractState)
        
        workflow.add_node("parse", self._parse_document)
        workflow.add_node("check_compliance", self._check_compliance)
        workflow.add_node("identify_risks", self._identify_risks)
        workflow.add_node("generate_summary", self._generate_summary)
        workflow.add_node("calculate_score", self._calculate_score)
        
        workflow.set_entry_point("parse")
        workflow.add_edge("parse", "check_compliance")
        workflow.add_edge("check_compliance", "identify_risks")
        workflow.add_edge("identify_risks", "generate_summary")
        workflow.add_edge("generate_summary", "calculate_score")
        workflow.add_edge("calculate_score", END)
        
        return workflow.compile()
    
    def _parse_document(self, state: ContractState) -> ContractState:
        """文档解析节点"""
        return state
    
    def _check_compliance(self, state: ContractState) -> ContractState:
        """合规性检查节点"""
        state["compliance"] = self.checker.check_compliance(state["text"])
        return state
    
    def _identify_risks(self, state: ContractState) -> ContractState:
        """风险识别节点"""
        state["risks"] = self.checker.identify_risks(state["text"])
        return state
    
    def _generate_summary(self, state: ContractState) -> ContractState:
        """生成摘要节点"""
        state["summary"] = self.llm_client.generate_summary(state["text"])
        return state
    
    def _calculate_score(self, state: ContractState) -> ContractState:
        """计算评分节点"""
        state["score"] = self.llm_client.calculate_risk_score(
            state["risks"], state["compliance"]
        )
        return state
    
    def analyze_contract(self, file_path: str) -> Dict:
        """分析合同"""
        # 解析文档
        if file_path.endswith('.pdf'):
            text = self.parser.parse_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self.parser.parse_docx(file_path)
        else:
            text = self.parser.parse_txt(file_path)
        
        # 执行工作流
        initial_state = ContractState(
            text=text,
            summary="",
            risks=[],
            compliance=[],
            score=0
        )
        
        result = self.graph.invoke(initial_state)
        
        return {
            "summary": result["summary"],
            "risks": result["risks"],
            "compliance": result["compliance"],
            "score": result["score"]
        }