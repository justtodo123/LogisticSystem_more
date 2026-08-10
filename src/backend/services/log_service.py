"""
埋点日志服务

功能：
1. 记录系统操作埋点
2. 写入 log_events 表
3. 支持的事件类型：login、logout、global_schedule、node_dispatch、route_plan、replan、deepseek_call
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from config.database import SessionLocal
from models.log_event import LogEvent

logger = logging.getLogger(__name__)

# 事件类型常量
EVENT_LOGIN = "login"
EVENT_LOGOUT = "logout"
EVENT_GLOBAL_SCHEDULE = "global_schedule"
EVENT_NODE_DISPATCH = "node_dispatch"
EVENT_ROUTE_PLAN = "route_plan"
EVENT_REPLAN = "replan"
EVENT_DEEPSEEK_CALL = "deepseek_call"
EVENT_SCHEDULE_CONFIRM = "schedule_confirm"
EVENT_SCHEDULE_DISCARD = "schedule_discard"
EVENT_EXCEPTION_RESOLVE = "exception_resolve"
EVENT_SCHEDULE_OVERRIDE = "schedule_override"
EVENT_BATCH_REPLAN = "batch_replan"

VALID_EVENTS = [
    EVENT_LOGIN, EVENT_LOGOUT, EVENT_GLOBAL_SCHEDULE,
    EVENT_NODE_DISPATCH, EVENT_ROUTE_PLAN, EVENT_REPLAN,
    EVENT_DEEPSEEK_CALL, EVENT_SCHEDULE_CONFIRM, EVENT_SCHEDULE_DISCARD,
    EVENT_EXCEPTION_RESOLVE, EVENT_SCHEDULE_OVERRIDE, EVENT_BATCH_REPLAN,
]


class LogService:
    """埋点日志服务"""
    
    @staticmethod
    def log_event(
        event_name: str,
        user_id: int,
        role: str,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Optional[Session] = None
    ) -> LogEvent:
        """
        记录埋点事件
        
        Args:
            event_name: 事件名称
            user_id: 用户ID
            role: 用户角色
            event_data: 事件附加数据（JSON格式）
            ip_address: 请求者IP地址
            user_agent: 请求者User-Agent
            db: 数据库会话（可选）
            
        Returns:
            LogEvent 对象
        """
        # 验证事件类型
        if event_name not in VALID_EVENTS:
            logger.warning(f"未知的事件类型：{event_name}")
        
        # 构建事件数据
        log_event = LogEvent(
            event_name=event_name,
            user_id=user_id,
            role=role,
            event_data=event_data or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # 写入数据库
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            db.add(log_event)
            db.commit()
            db.refresh(log_event)
            logger.info(f"埋点记录成功：{event_name}, user_id={user_id}")
            return log_event
        except Exception as e:
            db.rollback()
            logger.error(f"埋点记录失败：{e}")
            raise
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    def get_events(
        user_id: Optional[int] = None,
        event_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        db: Optional[Session] = None
    ) -> list[LogEvent]:
        """
        查询埋点记录
        
        Args:
            user_id: 按用户ID筛选
            event_name: 按事件类型筛选
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            db: 数据库会话（可选）
            
        Returns:
            LogEvent 对象列表
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            query = db.query(LogEvent)
            
            if user_id:
                query = query.filter(LogEvent.user_id == user_id)
            if event_name:
                query = query.filter(LogEvent.event_name == event_name)
            if start_time:
                query = query.filter(LogEvent.created_at >= start_time)
            if end_time:
                query = query.filter(LogEvent.created_at <= end_time)
            
            query = query.order_by(LogEvent.created_at.desc()).limit(limit)
            return query.all()
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    def cleanup_old_events(days: int = 30, db: Optional[Session] = None) -> int:
        """
        清理过期埋点记录
        
        Args:
            days: 保留天数（默认30天）
            db: 数据库会话（可选）
            
        Returns:
            删除的记录数
        """
        from datetime import timedelta
        
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            old_events = db.query(LogEvent).filter(LogEvent.created_at < cutoff_time).all()
            count = len(old_events)
            
            for event in old_events:
                db.delete(event)
            db.commit()
            
            logger.info(f"清理了 {count} 条过期埋点记录")
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"清理过期埋点记录失败：{e}")
            raise
        finally:
            if close_db:
                db.close()


def build_login_event_data(ip: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
    """构建登录事件的 event_data"""
    return {
        "ip": ip,
        "user_agent": user_agent
    }


def build_logout_event_data() -> Dict[str, Any]:
    """构建登出事件的 event_data"""
    return {}


def build_global_schedule_event_data(
    schedule_code: str,
    order_count: int,
    algorithm_type: str = "traditional"
) -> Dict[str, Any]:
    """构建全局调度事件的 event_data"""
    return {
        "schedule_code": schedule_code,
        "order_count": order_count,
        "algorithm_type": algorithm_type
    }


def build_node_dispatch_event_data(
    batch_code: str,
    package_count: int,
    vehicle_count: int,
    algorithm_type: str = "traditional"
) -> Dict[str, Any]:
    """构建节点间调度事件的 event_data"""
    return {
        "batch_code": batch_code,
        "package_count": package_count,
        "vehicle_count": vehicle_count,
        "algorithm_type": algorithm_type
    }


def build_route_plan_event_data(
    route_count: int,
    vehicle_count: int
) -> Dict[str, Any]:
    """构建路径规划事件的 event_data"""
    return {
        "route_count": route_count,
        "vehicle_count": vehicle_count
    }


def build_replan_event_data(
    event_code: str,
    reason: str,
    new_schedule_code: Optional[str] = None
) -> Dict[str, Any]:
    """构建重规划事件的 event_data"""
    return {
        "event_code": event_code,
        "reason": reason,
        "new_schedule_code": new_schedule_code
    }


def build_deepseek_call_event_data(
    function_name: str,
    success: bool,
    degraded: bool = False
) -> Dict[str, Any]:
    """构建DeepSeek调用事件的 event_data"""
    return {
        "function_name": function_name,
        "success": success,
        "degraded": degraded
    }


def build_schedule_confirm_event_data(
    schedule_code: str,
    order_count: int = 0
) -> Dict[str, Any]:
    """构建调度确认事件的 event_data"""
    return {
        "schedule_code": schedule_code,
        "order_count": order_count,
    }


def build_schedule_discard_event_data(
    schedule_code: str,
    reason: str = ""
) -> Dict[str, Any]:
    """构建调度废弃事件的 event_data"""
    return {
        "schedule_code": schedule_code,
        "reason": reason,
    }


def build_exception_resolve_event_data(
    event_code: str,
    action: str
) -> Dict[str, Any]:
    """构建异常处理事件的 event_data"""
    return {
        "event_code": event_code,
        "action": action,
    }
