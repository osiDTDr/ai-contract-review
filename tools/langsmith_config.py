import os
from langsmith import Client

def setup_langsmith():
    """配置LangSmith"""
    # 从环境变量获取配置
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT", "ai-contract-review")
    
    if api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        
        client = Client()
        return client
    
    return None

def get_trace_url(run_id: str) -> str:
    """获取LangSmith trace URL"""
    project = os.getenv("LANGCHAIN_PROJECT", "ai-contract-review")
    return f"https://smith.langchain.com/o/default/projects/p/{project}/r/{run_id}"