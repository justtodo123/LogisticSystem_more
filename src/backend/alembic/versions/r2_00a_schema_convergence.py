"""Converge Alembic heads and align formal schema with ORM

Revision ID: r2_00a_schema_convergence
Revises: c78f9b436833, phase7_exception_fields
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r2_00a_schema_convergence"
down_revision: Union[str, Sequence[str], None] = (
    "c78f9b436833",
    "phase7_exception_fields",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _converge_exception_events() -> None:
    """仅在遗留列无数据且当前字段完整时移除旧版异常字段。"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "exception_events" not in inspector.get_table_names():
        raise RuntimeError(
            "R2-00A convergence 需要 exception_events；检测到历史 revision 与实际 schema 不一致"
        )

    columns = {column["name"] for column in inspector.get_columns("exception_events")}
    legacy_columns = columns & {
        "trigger_node_id",
        "related_route_id",
        "severity",
        "resolution_note",
    }
    if not legacy_columns:
        return

    required_columns = {
        "event_code",
        "exception_type",
        "exception_subtype",
        "target_type",
        "target_code",
        "recommended_action",
        "related_schedule_code",
        "replan_batch_code",
        "description",
        "status",
        "resolved_at",
        "created_at",
    }
    missing_columns = required_columns - columns
    if missing_columns:
        detail = ", ".join(sorted(missing_columns))
        raise RuntimeError(
            "历史 exception_events 缺少目标字段，禁止自动收敛："
            f"{detail}；请复制数据库并人工修复"
        )

    quoted_table = bind.dialect.identifier_preparer.quote("exception_events")
    populated = []
    for column_name in sorted(legacy_columns):
        quoted_column = bind.dialect.identifier_preparer.quote(column_name)
        row = bind.execute(
            sa.text(
                f"SELECT 1 FROM {quoted_table} "
                f"WHERE {quoted_column} IS NOT NULL LIMIT 1"
            )
        ).first()
        if row is not None:
            populated.append(column_name)

    if populated:
        detail = ", ".join(populated)
        raise RuntimeError(
            "检测到历史 exception_events 遗留列含数据，禁止静默丢弃："
            f"{detail}；请复制数据库并执行人工映射/归档后再迁移"
        )

    with op.batch_alter_table("exception_events") as batch_op:
        for column_name in sorted(legacy_columns):
            batch_op.drop_column(column_name)


def upgrade() -> None:
    """补齐 ORM 正式对象，并把历史运行时 DDL 收敛到 Alembic。"""
    _converge_exception_events()

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("response_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_idempotency_records_idempotency_key"),
        "idempotency_records",
        ["idempotency_key"],
        unique=True,
    )

    op.create_table(
        "notification_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("enabled_channels", sa.JSON(), nullable=False),
        sa.Column("email_recipients", sa.JSON(), nullable=True),
        sa.Column("wechat_webhook_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ai_suggestions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("suggestion_code", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=16), server_default="info", nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("related_schedule_code", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("applied_schedule_code", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_by_role", sa.String(length=32), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decision_note", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_suggestions_suggestion_code"),
        "ai_suggestions",
        ["suggestion_code"],
        unique=True,
    )

    with op.batch_alter_table("dispatch_batches") as batch_op:
        batch_op.add_column(sa.Column("unallocated_packages", sa.String(length=2000), nullable=True))

    with op.batch_alter_table("vehicles") as batch_op:
        batch_op.add_column(sa.Column("plate_number", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("time_window_start", sa.Time(), nullable=True))
        batch_op.add_column(sa.Column("time_window_end", sa.Time(), nullable=True))
        batch_op.add_column(sa.Column("route_limit", sa.Integer(), server_default="5", nullable=False))
        batch_op.add_column(sa.Column("cost_per_km", sa.Float(), server_default="5.0", nullable=False))
        batch_op.add_column(sa.Column("load_rate_max", sa.Float(), server_default="0.9", nullable=False))

    with op.batch_alter_table("drivers") as batch_op:
        batch_op.add_column(sa.Column("shift_start", sa.Time(), nullable=True))
        batch_op.add_column(sa.Column("shift_end", sa.Time(), nullable=True))
        batch_op.add_column(sa.Column("max_drive_hours", sa.Float(), server_default="8.0", nullable=False))
        batch_op.add_column(sa.Column("max_continuous_hours", sa.Float(), server_default="4.0", nullable=False))

    with op.batch_alter_table("log_events") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.add_column(sa.Column("ip_address", sa.String(length=45), nullable=True))
        batch_op.add_column(sa.Column("user_agent", sa.String(length=512), nullable=True))

    with op.batch_alter_table("global_schedules") as batch_op:
        batch_op.add_column(sa.Column("explanation_data", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("undo_version", sa.Integer(), server_default="0", nullable=False))

    with op.batch_alter_table("node_dispatches") as batch_op:
        batch_op.add_column(sa.Column("override_snapshot", sa.JSON(), nullable=True))

    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=32),
            existing_nullable=False,
            server_default="unassigned",
        )

    op.create_index("ix_orders_status_dest", "orders", ["status", "destination_node_id"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    op.create_index("ix_goods_order_status", "goods", ["order_id", "status"])
    op.create_index(
        "ix_packages_from_to_status",
        "packages",
        ["from_node_id", "to_node_id", "status"],
    )
    op.create_index("ix_packages_schedule_id", "packages", ["schedule_id"])
    op.create_index(
        "ix_node_dispatches_batch_phase",
        "node_dispatches",
        ["dispatch_batch_id", "level_phase"],
    )
    op.create_index("ix_node_dispatches_vehicle_id", "node_dispatches", ["vehicle_id"])

    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("route_code", sa.String(length=64), nullable=False),
        sa.Column("dispatch_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("route_segments", sa.JSON(), nullable=False),
        sa.Column("total_distance", sa.DECIMAL(precision=12, scale=3), nullable=False),
        sa.Column("total_time", sa.DECIMAL(precision=12, scale=3), nullable=False),
        sa.Column("total_emission", sa.DECIMAL(precision=12, scale=4), nullable=False),
        sa.Column("algorithm_type", sa.String(length=32), server_default="traditional", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("replan_reason", sa.String(length=500), nullable=True),
        sa.Column("is_replan", sa.Boolean(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["dispatch_id"], ["node_dispatches.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["routes.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_routes_route_code"), "routes", ["route_code"], unique=True)


def downgrade() -> None:
    """回退本 revision 可安全逆转的 schema 对象。"""
    op.drop_index(op.f("ix_routes_route_code"), table_name="routes")
    op.drop_table("routes")

    op.drop_index("ix_node_dispatches_vehicle_id", table_name="node_dispatches")
    op.drop_index("ix_node_dispatches_batch_phase", table_name="node_dispatches")
    op.drop_index("ix_packages_schedule_id", table_name="packages")
    op.drop_index("ix_packages_from_to_status", table_name="packages")
    op.drop_index("ix_goods_order_status", table_name="goods")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_status_dest", table_name="orders")

    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=32),
            existing_nullable=False,
            server_default="pending",
        )

    with op.batch_alter_table("node_dispatches") as batch_op:
        batch_op.drop_column("override_snapshot")
    with op.batch_alter_table("global_schedules") as batch_op:
        batch_op.drop_column("undo_version")
        batch_op.drop_column("explanation_data")
    with op.batch_alter_table("log_events") as batch_op:
        batch_op.drop_column("user_agent")
        batch_op.drop_column("ip_address")
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
    with op.batch_alter_table("drivers") as batch_op:
        batch_op.drop_column("max_continuous_hours")
        batch_op.drop_column("max_drive_hours")
        batch_op.drop_column("shift_end")
        batch_op.drop_column("shift_start")
    with op.batch_alter_table("vehicles") as batch_op:
        batch_op.drop_column("load_rate_max")
        batch_op.drop_column("cost_per_km")
        batch_op.drop_column("route_limit")
        batch_op.drop_column("time_window_end")
        batch_op.drop_column("time_window_start")
        batch_op.drop_column("plate_number")
    with op.batch_alter_table("dispatch_batches") as batch_op:
        batch_op.drop_column("unallocated_packages")

    op.drop_index(op.f("ix_ai_suggestions_suggestion_code"), table_name="ai_suggestions")
    op.drop_table("ai_suggestions")
    op.drop_table("notification_configs")
    op.drop_index(
        op.f("ix_idempotency_records_idempotency_key"),
        table_name="idempotency_records",
    )
    op.drop_table("idempotency_records")
