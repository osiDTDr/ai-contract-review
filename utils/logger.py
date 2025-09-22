import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class StepStatus(Enum):
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

@dataclass
class ProcessStep:
    step_id: str
    name: str
    description: str
    status: StepStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ProcessLogger:
    def __init__(self, process_name: str, session_id: str = None):
        self.process_name = process_name
        self.session_id = session_id or f"{process_name}_{int(time.time())}"
        self.steps: List[ProcessStep] = []
        self.current_step: Optional[ProcessStep] = None
        self.start_time = time.time()
        
        # 配置标准日志
        self.logger = logging.getLogger(f"ProcessLogger.{process_name}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @contextmanager
    def step(self, step_id: str, name: str, description: str = "", **metadata):
        """步骤上下文管理器"""
        step = ProcessStep(
            step_id=step_id,
            name=name,
            description=description,
            status=StepStatus.STARTED,
            start_time=time.time(),
            metadata=metadata
        )
        
        self.current_step = step
        self.steps.append(step)
        
        self.logger.info(f"🚀 开始步骤: {name} ({step_id})")
        if description:
            self.logger.info(f"   描述: {description}")
        
        try:
            step.status = StepStatus.IN_PROGRESS
            yield step
            
            step.status = StepStatus.COMPLETED
            step.end_time = time.time()
            step.duration = step.end_time - step.start_time
            
            self.logger.info(f"✅ 完成步骤: {name} (耗时: {step.duration:.2f}s)")
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.end_time = time.time()
            step.duration = step.end_time - step.start_time
            step.error = str(e)
            
            self.logger.error(f"❌ 步骤失败: {name} - {str(e)}")
            raise
        finally:
            self.current_step = None
    
    def log_input(self, data: Dict[str, Any]):
        """记录当前步骤的输入数据"""
        if self.current_step:
            self.current_step.input_data = data
            self.logger.debug(f"📥 输入数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def log_output(self, data: Dict[str, Any]):
        """记录当前步骤的输出数据"""
        if self.current_step:
            self.current_step.output_data = data
            self.logger.debug(f"📤 输出数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def log_progress(self, message: str, progress: float = None):
        """记录进度信息"""
        if progress is not None:
            self.logger.info(f"⏳ {message} ({progress:.1%})")
        else:
            self.logger.info(f"⏳ {message}")
    
    def log_metric(self, name: str, value: Any, unit: str = ""):
        """记录指标"""
        self.logger.info(f"📊 {name}: {value} {unit}")
    
    def log_warning(self, message: str):
        """记录警告"""
        self.logger.warning(f"⚠️  {message}")
    
    def log_error(self, message: str, error: Exception = None):
        """记录错误"""
        if error:
            self.logger.error(f"🚨 {message}: {str(error)}")
        else:
            self.logger.error(f"🚨 {message}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        total_duration = time.time() - self.start_time
        completed_steps = [s for s in self.steps if s.status == StepStatus.COMPLETED]
        failed_steps = [s for s in self.steps if s.status == StepStatus.FAILED]
        
        return {
            "session_id": self.session_id,
            "process_name": self.process_name,
            "total_duration": total_duration,
            "total_steps": len(self.steps),
            "completed_steps": len(completed_steps),
            "failed_steps": len(failed_steps),
            "success_rate": len(completed_steps) / len(self.steps) if self.steps else 0,
            "steps": [asdict(step) for step in self.steps]
        }
    
    def export_trace(self) -> str:
        """导出完整执行轨迹"""
        summary = self.get_summary()
        return json.dumps(summary, ensure_ascii=False, indent=2, default=str)
    
    def print_summary(self):
        """打印执行摘要"""
        summary = self.get_summary()
        
        print(f"\n{'='*60}")
        print(f"🎯 执行摘要 - {self.process_name}")
        print(f"{'='*60}")
        print(f"会话ID: {self.session_id}")
        print(f"总耗时: {summary['total_duration']:.2f}s")
        print(f"总步骤: {summary['total_steps']}")
        print(f"成功步骤: {summary['completed_steps']}")
        print(f"失败步骤: {summary['failed_steps']}")
        print(f"成功率: {summary['success_rate']:.1%}")
        
        print(f"\n📋 步骤详情:")
        for step in self.steps:
            status_icon = {
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.IN_PROGRESS: "⏳",
                StepStatus.STARTED: "🚀",
                StepStatus.SKIPPED: "⏭️"
            }.get(step.status, "❓")
            
            duration_str = f"{step.duration:.2f}s" if step.duration else "N/A"
            print(f"  {status_icon} {step.name} ({step.step_id}) - {duration_str}")
            if step.error:
                print(f"     ❌ 错误: {step.error}")
        
        print(f"{'='*60}\n")