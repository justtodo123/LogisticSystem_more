"""正式 ORM 模型注册表。

Alembic、运行时和测试通过本模块加载同一组模型，避免依赖零散导入的
副作用来填充 ``Base.metadata``。
"""

from .ai_suggestion import AiSuggestion
from .code_range import CodeRange
from .dispatch_batch import DispatchBatch
from .driver import Driver
from .exception_event import ExceptionEvent
from .global_schedule import GlobalSchedule
from .goods import Goods
from .idempotency_record import IdempotencyRecord
from .log_event import LogEvent
from .node import Node
from .node_dispatch import NodeDispatch
from .notification_config import NotificationConfig
from .order import Order
from .package import Package
from .route import Route
from .replan_task import ReplanTask
from .sorting_center import SortingCenter
from .storage_center import StorageCenter
from .user import User
from .vehicle import Vehicle

MODEL_REGISTRY = (
    User,
    LogEvent,
    Node,
    StorageCenter,
    SortingCenter,
    Order,
    Goods,
    Package,
    Vehicle,
    Driver,
    GlobalSchedule,
    DispatchBatch,
    NodeDispatch,
    Route,
    ReplanTask,
    ExceptionEvent,
    IdempotencyRecord,
    NotificationConfig,
    AiSuggestion,
    CodeRange,
)

MODEL_TABLE_NAMES = frozenset(model.__tablename__ for model in MODEL_REGISTRY)


def import_all_models() -> tuple[type, ...]:
    """返回完整模型注册表，并确保对应表已加载到共享 metadata。"""
    return MODEL_REGISTRY


__all__ = [
    "MODEL_REGISTRY",
    "MODEL_TABLE_NAMES",
    "import_all_models",
    *(model.__name__ for model in MODEL_REGISTRY),
]
