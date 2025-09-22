from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
import tempfile
import os
import json
import asyncio
from agent.contract_agent import ContractReviewAgent
from tools.reasoning_visualizer import ReasoningTraceVisualizer
from tools.langsmith_config import setup_langsmith, get_trace_url
from langsmith import get_current_run_tree

# 初始化LangSmith
setup_langsmith()

app = FastAPI(title="AI Contract Review", version="1.0.0")
agent = ContractReviewAgent()

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze_contract(file: UploadFile = File(...)):
    """合同分析接口 - 流式返回推理日志和结果"""
    # 检查文件类型
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型。支持的类型: {', '.join(allowed_types)}"
        )
    
    # 在生成器外部读取文件内容
    content = await file.read()
    
    async def generate_stream():
        tmp_file_path = None
        try:
            # 保存临时文件
            fd, tmp_file_path = tempfile.mkstemp(suffix=file_ext)
            with os.fdopen(fd, 'wb') as tmp_file:
                tmp_file.write(content)
            
            yield f"data: {json.dumps({'type': 'start', 'message': '开始分析合同...'}, ensure_ascii=False)}\n\n"
            
            # 流式分析合同
            async for chunk in agent.analyze_contract_stream(tmp_file_path):
                yield f"data: {json.dumps(chunk, default=str, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)  # 小延迟保证流式传输
            
            yield f"data: {json.dumps({'type': 'complete', 'message': '分析完成'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'分析失败: {str(e)}'}, ensure_ascii=False)}\n\n"
        finally:
            # 清理临时文件
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.post("/analyze/trace")
async def get_reasoning_trace(file: UploadFile = File(...)):
    """获取推理轨迹可视化"""
    # 检查文件类型
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型。支持的类型: {', '.join(allowed_types)}"
        )
    
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # 分析合同并获取轨迹
        result = agent.analyze_contract_with_trace(tmp_file_path)
        
        # 获取LangSmith trace信息
        try:
            run_tree = get_current_run_tree()
            trace_url = get_trace_url(run_tree.id) if run_tree else None
        except:
            trace_url = None
        
        # 清理临时文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        # 生成HTML可视化
        html_trace = ReasoningTraceVisualizer.format_langgraph_trace(result.get('reasoning_trace', []))
        
        # 添加LangSmith链接
        langsmith_link = f'<p><a href="{trace_url}" target="_blank">查看LangSmith详细轨迹</a></p>' if trace_url else ''
        
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI合同审查推理轨迹</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .reasoning-trace {{ max-width: 800px; margin: 0 auto; }}
                .step {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .meta {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
                .confidence {{ margin-left: 20px; font-weight: bold; }}
                .content p {{ margin: 5px 0; }}
                h2 {{ color: #333; text-align: center; }}
                h3 {{ color: #555; margin-top: 0; }}
                .langsmith-link {{ text-align: center; margin: 20px 0; }}
                .langsmith-link a {{ color: #007bff; text-decoration: none; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="langsmith-link">{langsmith_link}</div>
            {html_trace}
        </body>
        </html>
        """)
        
    except Exception as e:
        # 清理临时文件
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)