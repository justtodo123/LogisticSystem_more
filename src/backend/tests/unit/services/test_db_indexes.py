"""
T4-2 数据库索引优化测试

验证 Alembic fresh upgrade 创建的索引：
1. 7 个预期索引全部存在
2. EXPLAIN QUERY PLAN 显示高频查询走索引而非全表扫描
3. 1000 条数据规模下订单列表分页查询耗时达标（<100ms 安全阈值，本地实测远低于 50ms）
"""
import time

import pytest
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.database_url import engine_connect_args
from utils.schema_management import alembic_config, sqlite_database_url


EXPECTED_INDEXES = {
    "ix_orders_status_dest": "orders",
    "ix_orders_created_at": "orders",
    "ix_goods_order_status": "goods",
    "ix_packages_from_to_status": "packages",
    "ix_packages_schedule_id": "packages",
    "ix_node_dispatches_batch_phase": "node_dispatches",
    "ix_node_dispatches_vehicle_id": "node_dispatches",
}


@pytest.fixture(scope="function")
def test_db(tmp_path):
    """通过 Alembic 在临时文件数据库中构建正式 schema。"""
    database_url = sqlite_database_url(tmp_path / "indexes.db")
    command.upgrade(alembic_config(database_url), "head")
    engine = create_engine(
        database_url,
        connect_args=engine_connect_args(database_url),
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    try:
        yield engine, testing_session_local
    finally:
        engine.dispose()


def _index_names(engine, table):
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA index_list({table})")).fetchall()
        return {r[1] for r in rows}


def _seed_orders(engine, count):
    """直接批量插入 orders 数据（绕过 ORM，仅用于查询计划/性能验证）"""
    with engine.connect() as conn:
        conn.execute(text(
            f"WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM seq WHERE n < {count}) "
            f"INSERT INTO orders (order_code, destination_node_id, time_window, status, created_at) "
            f"SELECT 'BULK' || n, 1, '2026-06-15 全天', 'unassigned', datetime('now', '-' || (n % 100) || ' days') "
            f"FROM seq"
        ))
        conn.commit()


@pytest.mark.unit
class TestPhase4Indexes:
    def test_all_expected_indexes_created(self, test_db):
        """7 个高频查询索引全部创建"""
        engine, _ = test_db
        for index_name, table in EXPECTED_INDEXES.items():
            assert index_name in _index_names(engine, table), f"索引 {index_name}({table}) 未创建"

    def test_orders_filter_uses_index(self, test_db):
        """订单按状态+目的地过滤走复合索引"""
        engine, _ = test_db
        _seed_orders(engine, 300)
        with engine.connect() as conn:
            plan = conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT * FROM orders "
                "WHERE status='unassigned' AND destination_node_id=1"
            )).fetchall()
        detail = " ".join(r[3] for r in plan)
        assert "ix_orders_status_dest" in detail, f"未走复合索引: {detail}"

    def test_orders_sort_uses_index(self, test_db):
        """订单列表按创建时间排序走索引"""
        engine, _ = test_db
        _seed_orders(engine, 300)
        with engine.connect() as conn:
            plan = conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT * FROM orders ORDER BY created_at DESC LIMIT 20"
            )).fetchall()
        detail = " ".join(r[3] for r in plan)
        assert "ix_orders_created_at" in detail, f"未走创建时间索引: {detail}"

    def test_goods_filter_uses_index(self, test_db, test_goods):
        """货物按订单+状态过滤走复合索引"""
        engine, _ = test_db
        order_id = test_goods["G001"].order_id
        with engine.connect() as conn:
            plan = conn.execute(text(
                f"EXPLAIN QUERY PLAN SELECT * FROM goods "
                f"WHERE order_id={order_id} AND status='pending_pack'"
            )).fetchall()
        detail = " ".join(r[3] for r in plan)
        assert "ix_goods_order_status" in detail, f"未走复合索引: {detail}"

    def test_packages_route_uses_index(self, test_db):
        """包裹按起终点+状态过滤走复合索引"""
        engine, _ = test_db
        with engine.connect() as conn:
            plan = conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT * FROM packages "
                "WHERE from_node_id=1 AND to_node_id=2 AND status='in_transit'"
            )).fetchall()
        detail = " ".join(r[3] for r in plan)
        assert "ix_packages_from_to_status" in detail, f"未走复合索引: {detail}"

    def test_packages_schedule_uses_index(self, test_db):
        """包裹按调度方案过滤走索引"""
        engine, _ = test_db
        with engine.connect() as conn:
            plan = conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT * FROM packages WHERE schedule_id=10"
            )).fetchall()
        detail = " ".join(r[3] for r in plan)
        assert "ix_packages_schedule_id" in detail, f"未走 schedule_id 索引: {detail}"

    def test_node_dispatches_batch_phase_uses_index(self, test_db):
        """调度单按批次+层级过滤走复合索引"""
        engine, _ = test_db
        with engine.connect() as conn:
            plan = conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT * FROM node_dispatches "
                "WHERE dispatch_batch_id=1 AND level_phase=0"
            )).fetchall()
        detail = " ".join(r[3] for r in plan)
        assert "ix_node_dispatches_batch_phase" in detail, f"未走复合索引: {detail}"

    def test_node_dispatches_vehicle_uses_index(self, test_db):
        """调度单按车辆过滤走索引（模型无 status 列，退化为单列索引）"""
        engine, _ = test_db
        with engine.connect() as conn:
            plan = conn.execute(text(
                "EXPLAIN QUERY PLAN SELECT * FROM node_dispatches WHERE vehicle_id=1"
            )).fetchall()
        detail = " ".join(r[3] for r in plan)
        assert "ix_node_dispatches_vehicle_id" in detail, f"未走 vehicle_id 索引: {detail}"

    def test_order_list_pagination_1000_rows(self, test_db):
        """1000 条数据规模下订单分页查询走索引且耗时达标（<100ms）"""
        engine, _ = test_db
        _seed_orders(engine, 1000)
        query = (
            "SELECT * FROM orders "
            "WHERE status='unassigned' AND destination_node_id=1 "
            "ORDER BY created_at DESC LIMIT 20 OFFSET 0"
        )
        with engine.connect() as conn:
            plan = conn.execute(text(f"EXPLAIN QUERY PLAN {query}")).fetchall()
            detail = " ".join(r[3] for r in plan)
            # 过滤条件走复合索引（排序在索引结果上完成）
            assert "ix_orders_status_dest" in detail, f"未走复合索引: {detail}"

            # 预热 + 计时
            conn.execute(text(query)).fetchall()
            start = time.monotonic()
            for _ in range(50):
                conn.execute(text(query)).fetchall()
            elapsed_ms = (time.monotonic() - start) * 1000 / 50
            assert elapsed_ms < 100, f"分页查询平均耗时 {elapsed_ms:.2f}ms，超过 100ms 阈值"
