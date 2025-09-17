from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_ollama import ChatOllama
from config import settings


class LLMClient:
    def __init__(self):
        self.llm = self._create_llm()

    def _create_llm(self):
        """根据配置创建LLM客户端"""
        if settings.llm_provider == "openai":
            return ChatOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model="gpt-3.5-turbo"
            )
        elif settings.llm_provider == "azure":
            return AzureChatOpenAI(
                azure_endpoint=settings.azure_endpoint,
                api_key=settings.azure_api_key,
                azure_deployment=settings.azure_deployment,
                api_version="2023-12-01-preview"
            )
        elif settings.llm_provider == "ollama":
            return ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model
            )

    def generate_summary(self, text: str) -> str:
        """生成合同摘要"""
        prompt = f"请对以下合同内容生成简要摘要：\n{text[:2000]}"
        return self.llm.invoke(prompt).content

    def calculate_risk_score(self, risks: list, compliance: list) -> int:
        """计算风险评分"""
        risk_count = len([r for r in risks if r['severity'] == 'high']) * 3 + \
                     len([r for r in risks if r['severity'] == 'medium']) * 2
        compliance_issues = len([c for c in compliance if "缺少" in c])

        base_score = 10
        penalty = min(risk_count + compliance_issues * 2, 8)
        return max(base_score - penalty, 1)
