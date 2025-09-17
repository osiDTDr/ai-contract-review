from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from agent.contract_agent import ContractReviewAgent

app = FastAPI(title="AI Contract Review", version="1.0.0")
agent = ContractReviewAgent()

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze_contract(file: UploadFile = File(...)):
    """合同分析接口"""
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
        
        # 分析合同
        result = agent.analyze_contract(tmp_file_path)
        
        # 清理临时文件
        os.unlink(tmp_file_path)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        # 清理临时文件
        if 'tmp_file_path' in locals():
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)