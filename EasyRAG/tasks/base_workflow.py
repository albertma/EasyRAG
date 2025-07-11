from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import logging
from datetime import datetime
from celery import current_task

logger = logging.getLogger(__name__)


class WorkflowStepStatus(Enum):
    """工作流步骤状态"""
    PENDING = "PENDING"      # 待执行
    RUNNING = "RUNNING"      # 执行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"        # 失败
    SKIPPED = "SKIPPED"      # 跳过
    CANCELLED = "CANCELLED"  # 已取消


class WorkflowStep(ABC):
    """工作流步骤抽象基类"""
    
    def __init__(self, step_name: str, step_config: Dict[str, Any] = None):
        self.step_name = step_name
        self.step_config = step_config or {}
        self.status = WorkflowStepStatus.PENDING
        self.progress = 0.0
        self.message = ""
        self.start_time = None
        self.end_time = None
        self.error = None
        self.result = None
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行步骤"""
        pass
    
    def update_progress(self, progress: float, message: str = ""):
        """更新进度"""
        self.progress = progress
        self.message = message
        
        # 更新Celery任务状态
        if current_task:
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'step': self.step_name,
                    'progress': progress,
                    'message': message
                }
            )
    
    def start(self):
        """开始执行"""
        self.status = WorkflowStepStatus.RUNNING
        self.start_time = datetime.now()
        self.update_progress(0.0, f"开始执行步骤: {self.step_name}")
    
    def complete(self, result: Dict[str, Any] = None):
        """完成执行"""
        self.status = WorkflowStepStatus.COMPLETED
        self.end_time = datetime.now()
        self.progress = 100.0
        self.result = result
        self.update_progress(100.0, f"步骤完成: {self.step_name}")
    
    def fail(self, error: str):
        """执行失败"""
        self.status = WorkflowStepStatus.FAILED
        self.end_time = datetime.now()
        self.error = error
        self.update_progress(0.0, f"步骤失败: {self.step_name} - {error}")
    
    def skip(self, reason: str = ""):
        """跳过执行"""
        self.status = WorkflowStepStatus.SKIPPED
        self.end_time = datetime.now()
        self.message = f"步骤跳过: {self.step_name} - {reason}"
        self.update_progress(100.0, self.message)


class BaseWorkflow(ABC):
    """基础工作流抽象类"""
    
    def __init__(self, workflow_config: Dict[str, Any] = None):
        self.workflow_config = workflow_config or {}
        self.steps: List[WorkflowStep] = []
        self.context: Dict[str, Any] = {}
        self.current_step_index = 0
        self.is_cancelled = False
        
    @abstractmethod
    def get_workflow_steps(self) -> List[WorkflowStep]:
        """获取工作流步骤列表"""
        pass
    
    def add_step(self, step: WorkflowStep):
        """添加步骤"""
        self.steps.append(step)
    
    def remove_step(self, step_name: str):
        """移除步骤"""
        self.steps = [step for step in self.steps if step.step_name != step_name]
    
    def get_step(self, step_name: str) -> Optional[WorkflowStep]:
        """获取指定步骤"""
        for step in self.steps:
            if step.step_name == step_name:
                return step
        return None
    
    def execute(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行工作流"""
        self.context = initial_context or {}
        self.current_step_index = 0
        
        try:
            # 初始化步骤
            if not self.steps:
                self.steps = self.get_workflow_steps()
            
            # 执行每个步骤
            for i, step in enumerate(self.steps):
                if self.is_cancelled:
                    logger.info("工作流已被取消")
                    break
                
                self.current_step_index = i
                logger.info(f"执行步骤 {i+1}/{len(self.steps)}: {step.step_name}")
                
                try:
                    # 检查步骤是否应该执行
                    if not self._should_execute_step(step):
                        step.skip("步骤配置为跳过")
                        continue
                    
                    # 执行步骤
                    step.start()
                    result = step.execute(self.context)
                    step.complete(result)
                    
                    # 更新上下文
                    self.context.update(result)
                    
                    logger.info(f"步骤 {step.step_name} 执行完成")
                    
                except Exception as e:
                    logger.error(f"步骤 {step.step_name} 执行失败: {e}")
                    step.fail(str(e))
                    raise
            
            return {
                "success": True,
                "context": self.context,
                "steps": [self._step_to_dict(step) for step in self.steps]
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": self.context,
                "steps": [self._step_to_dict(step) for step in self.steps]
            }
    
    def _should_execute_step(self, step: WorkflowStep) -> bool:
        """检查步骤是否应该执行"""
        # 可以从配置中读取步骤的执行条件
        step_config = self.workflow_config.get("steps", {}).get(step.step_name, {})
        return step_config.get("enabled", True)
    
    def _step_to_dict(self, step: WorkflowStep) -> Dict[str, Any]:
        """将步骤转换为字典"""
        return {
            "step_name": step.step_name,
            "status": step.status.value,
            "progress": step.progress,
            "message": step.message,
            "start_time": step.start_time.isoformat() if step.start_time else None,
            "end_time": step.end_time.isoformat() if step.end_time else None,
            "error": step.error,
            "result": step.result
        }
    
    def cancel(self):
        """取消工作流"""
        self.is_cancelled = True
        logger.info("工作流取消请求已发送")
    
    def get_progress(self) -> Dict[str, Any]:
        """获取工作流进度"""
        completed_steps = sum(1 for step in self.steps if step.status == WorkflowStepStatus.COMPLETED)
        total_steps = len(self.steps)
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            "progress": progress,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "current_step": self.steps[self.current_step_index].step_name if self.steps and self.current_step_index < len(self.steps) else None,
            "steps": [self._step_to_dict(step) for step in self.steps]
        }
