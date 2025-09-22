from typing import List, Dict

class ReasoningTraceVisualizer:
    """推理轨迹可视化工具"""
    
    @staticmethod
    def format_trace_text(reasoning_trace: List[Dict]) -> str:
        """格式化推理轨迹为文本"""
        output = []
        output.append("=" * 60)
        output.append("AI 合同审查推理轨迹")
        output.append("=" * 60)
        
        for i, step in enumerate(reasoning_trace, 1):
            output.append(f"\n步骤 {i}: {step['step']}")
            output.append(f"时间: {step['timestamp']}")
            output.append(f"置信度: {step['confidence']:.2%}")
            output.append(f"输入: {step['input_summary']}")
            output.append(f"推理: {step['reasoning']}")
            output.append(f"输出: {step['output_summary']}")
            output.append("-" * 40)
        
        return "\n".join(output)
    
    @staticmethod
    def format_trace_html(reasoning_trace: List[Dict]) -> str:
        """格式化推理轨迹为HTML"""
        html = """
        <div class="reasoning-trace">
            <h2>AI 合同审查推理轨迹</h2>
        """
        
        for i, step in enumerate(reasoning_trace, 1):
            confidence_color = "green" if step['confidence'] > 0.8 else "orange" if step['confidence'] > 0.6 else "red"
            
            html += f"""
            <div class="step">
                <h3>步骤 {i}: {step['step']}</h3>
                <div class="meta">
                    <span class="timestamp">时间: {step['timestamp']}</span>
                    <span class="confidence" style="color: {confidence_color}">
                        置信度: {step['confidence']:.2%}
                    </span>
                </div>
                <div class="content">
                    <p><strong>输入:</strong> {step['input_summary']}</p>
                    <p><strong>推理:</strong> {step['reasoning']}</p>
                    <p><strong>输出:</strong> {step['output_summary']}</p>
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    @staticmethod
    def format_langgraph_trace(trace_log: List[Dict]) -> str:
        """格式化LangGraph轨迹为HTML"""
        html = """
        <div class="reasoning-trace">
            <h2>AI 合同审查执行轨迹</h2>
        """
        
        for i, chunk in enumerate(trace_log, 1):
            if '__end__' in chunk:
                continue
                
            node_name = list(chunk.keys())[0]
            node_data = chunk[node_name]
            
            html += f"""
            <div class="step">
                <h3>步骤 {i}: {node_name}</h3>
                <div class="content">
                    <p><strong>状态更新:</strong></p>
                    <ul>
            """
            
            # 显示状态变化
            for key, value in node_data.items():
                if key == 'text':
                    html += f"<li>文档长度: {len(str(value))} 字符</li>"
                elif key == 'knowledge_context':
                    html += f"<li>知识库检索: {len(value)} 条相关知识</li>"
                elif key == 'compliance':
                    html += f"<li>合规检查: {len(value)} 项问题</li>"
                elif key == 'risks':
                    html += f"<li>风险识别: {len(value)} 个风险点</li>"
                elif key == 'summary':
                    html += f"<li>摘要生成: {len(str(value))} 字符</li>"
                elif key == 'score':
                    html += f"<li>风险评分: {value}/10</li>"
            
            html += """
                    </ul>
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    @staticmethod
    def get_trace_summary(trace_log: List[Dict]) -> Dict:
        """获取LangGraph轨迹摘要"""
        if not trace_log:
            return {"total_steps": 0, "nodes_executed": []}
        
        nodes_executed = []
        for chunk in trace_log:
            if '__end__' not in chunk:
                nodes_executed.extend(chunk.keys())
        
        return {
            "total_steps": len(nodes_executed),
            "nodes_executed": nodes_executed
        }