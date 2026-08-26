from models.base import Base
from models.registry import MODEL_REGISTRY, MODEL_TABLE_NAMES, import_all_models


EXPECTED_MODEL_TABLES = {
    "users",
    "log_events",
    "nodes",
    "storage_centers",
    "sorting_centers",
    "orders",
    "goods",
    "packages",
    "vehicles",
    "drivers",
    "global_schedules",
    "dispatch_batches",
    "node_dispatches",
    "routes",
    "exception_events",
    "idempotency_records",
    "notification_configs",
    "ai_suggestions",
}


def test_model_registry_is_complete_and_unique():
    assert len(MODEL_REGISTRY) == 18
    assert len(set(MODEL_REGISTRY)) == len(MODEL_REGISTRY)
    assert MODEL_TABLE_NAMES == EXPECTED_MODEL_TABLES


def test_registry_populates_shared_metadata():
    assert import_all_models() is MODEL_REGISTRY
    assert set(Base.metadata.tables) == EXPECTED_MODEL_TABLES
    assert {model.metadata for model in MODEL_REGISTRY} == {Base.metadata}
