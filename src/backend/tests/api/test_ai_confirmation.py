"""
API测试：AI 建议确认闸门（T6-2）

覆盖：
- POST /api/ai/parse 成功后创建 AiSuggestion（level=suggestion，pending）并返回 suggestion_id
- POST /api/ai/suggestions/{id}/confirm：suggestion 级别触发实际调度修改（draft → active + F021 打包）
- POST /api/ai/suggestions/{id}/reject：仅记录，不触发调度修改
- 重复确认/拒绝、不存在建议、非法状态过滤、权限控制
- info 级别建议确认不执行调度修改
- 确认/拒绝写入 log_events 审计
"""
import pytest
from models.user import User
from models.node import Node
from models.storage_center import StorageCenter
from models.sorting_center import SortingCenter
from models.order import Order
from models.goods import Goods
from models.global_schedule import GlobalSchedule
from models.log_event import LogEvent


def _build_topology(db_session):
    """构建 L0/L1/L2 节点 + 订单 + 货物（参考 test_schedule.py 全链路）"""
    # L0 存储中心
    node_sc1 = Node(
        node_code="SC001", name="存储中心1", location="测试",
        latitude=30.5, longitude=114.3, node_type="storage_center",
    )
    node_sc2 = Node(
        node_code="SC002", name="存储中心2", location="测试",
        latitude=28.2, longitude=112.9, node_type="storage_center",
    )
    db_session.add_all([node_sc1, node_sc2])
    db_session.flush()
    db_session.add_all([
        StorageCenter(node_id=node_sc1.id, capacity=1000.0, inventory=0),
        StorageCenter(node_id=node_sc2.id, capacity=800.0, inventory=0),
    ])

    # L1 分拣中心
    node_so1 = Node(
        node_code="SO001", name="分拣中心1", location="测试",
        latitude=30.6, longitude=114.4, node_type="sorting_center",
    )
    node_so2 = Node(
        node_code="SO002", name="分拣中心2", location="测试",
        latitude=28.3, longitude=112.8, node_type="sorting_center",
    )
    db_session.add_all([node_so1, node_so2])
    db_session.flush()
    db_session.add_all([
        SortingCenter(node_id=node_so1.id, level=1, capacity=100, max_storage_time=24),
        SortingCenter(node_id=node_so2.id, level=1, capacity=100, max_storage_time=24),
    ])

    # L2 目的地
    node_dest1 = Node(
        node_code="SO010", name="目的地1", location="测试",
        latitude=30.54, longitude=114.315, node_type="sorting_center",
    )
    node_dest2 = Node(
        node_code="SO011", name="目的地2", location="测试",
        latitude=30.61, longitude=114.28, node_type="sorting_center",
    )
    db_session.add_all([node_dest1, node_dest2])
    db_session.flush()
    db_session.add_all([
        SortingCenter(node_id=node_dest1.id, level=0),
        SortingCenter(node_id=node_dest2.id, level=0),
    ])

    # 订单 + 货物
    order1 = Order(
        order_code="O001", destination_node_id=node_dest1.id,
        time_window="全天", status="unassigned",
    )
    order2 = Order(
        order_code="O002", destination_node_id=node_dest2.id,
        time_window="全天", status="unassigned",
    )
    db_session.add_all([order1, order2])
    db_session.flush()

    db_session.add_all([
        Goods(
            goods_code="G001", goods_name="测试货物1", goods_type="普通",
            weight=10.0, volume=0.5, node_id=node_sc1.id,
            order_id=order1.id, status="pending_pack",
        ),
        Goods(
            goods_code="G002", goods_name="测试货物2", goods_type="普通",
            weight=5.0, volume=0.3, node_id=node_sc1.id,
            order_id=order2.id, status="pending_pack",
        ),
    ])
    db_session.commit()
    return [order1, order2]


_MANUAL_WEIGHTS = {
    "global_schedule": {
        "algorithm": "traditional",
        "weights": {"distance": 0.5, "time": 0.3, "package_count": 0.2},
    }
}


@pytest.fixture
def auth_headers(client, test_users):
    """调度员认证头"""
    response = client.post("/api/auth/login", json={
        "username": "dispatcher", "password": "123456",
    })
    assert response.status_code == 200, f"登录失败: {response.json()}"
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers(client, test_users):
    """管理者认证头"""
    response = client.post("/api/auth/login", json={
        "username": "manager", "password": "123456",
    })
    assert response.status_code == 200, f"登录失败: {response.json()}"
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _parse_draft(client, headers):
    """调用 /api/ai/parse（手动权重，mode=manual，无需 DeepSeek）→ 返回 (response_body, suggestion_id)"""
    response = client.post(
        "/api/ai/parse",
        json={"execute": "draft", "weights": _MANUAL_WEIGHTS},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0, f"parse 失败: {body}"
    data = body["data"]
    assert data["status"] == "draft"
    assert data["suggestion_level"] == "suggestion"
    return body, data["suggestion_id"]


class TestParseCreatesSuggestion:
    """parse 成功后创建 AiSuggestion 建议记录"""

    @pytest.mark.api
    def test_parse_creates_pending_suggestion(self, client, auth_headers, db_session):
        """parse 返回 suggestion_id/suggestion_level，落库一条 pending 建议"""
        _build_topology(db_session)

        body, suggestion_id = _parse_draft(client, auth_headers)

        # 响应携带建议信息
        assert suggestion_id is not None

        # 落库校验
        from models.ai_suggestion import AiSuggestion
        suggestion = db_session.query(AiSuggestion).filter(
            AiSuggestion.id == suggestion_id
        ).first()
        assert suggestion is not None
        assert suggestion.status == "pending"
        assert suggestion.level == "suggestion"
        assert suggestion.source == "parse"
        assert suggestion.related_schedule_code == body["data"]["schedule_code"]
        assert suggestion.payload["global_schedule"]["weights"]["distance"] == 0.5

    @pytest.mark.api
    def test_parse_dry_run_no_suggestion(self, client, auth_headers, db_session):
        """dry-run 模式不创建建议（不落库）"""
        _build_topology(db_session)
        response = client.post(
            "/api/ai/parse",
            json={"execute": "dry-run", "weights": _MANUAL_WEIGHTS},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"].get("suggestion_id") is None

        from models.ai_suggestion import AiSuggestion
        count = db_session.query(AiSuggestion).count()
        assert count == 0


class TestConfirmSuggestion:
    """确认建议 → 触发实际调度修改（draft → active + F021 打包）"""

    @pytest.mark.api
    def test_confirm_applies_schedule(self, client, auth_headers, db_session):
        """confirm 后：建议 confirmed + applied_schedule_code、方案 active、产生包裹、审计日志"""
        _build_topology(db_session)
        body, suggestion_id = _parse_draft(client, auth_headers)
        schedule_code = body["data"]["schedule_code"]

        response = client.post(
            f"/api/ai/suggestions/{suggestion_id}/confirm",
            headers=auth_headers,
        )
        assert response.status_code == 200
        confirm_body = response.json()
        assert confirm_body["code"] == 0, f"confirm 失败: {confirm_body}"
        assert confirm_body["data"]["applied_schedule_code"] == schedule_code
        assert confirm_body["data"]["suggestion"]["status"] == "confirmed"

        # 调度方案 draft → active，且已打包
        gs = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        assert gs is not None
        assert gs.status == "active"

        from models.package import Package
        pkg_count = db_session.query(Package).filter(Package.schedule_id == gs.id).count()
        assert pkg_count > 0

        # 审计日志
        from services.log_service import EVENT_AI_SUGGESTION_CONFIRM
        audit = db_session.query(LogEvent).filter(
            LogEvent.event_name == EVENT_AI_SUGGESTION_CONFIRM
        ).first()
        assert audit is not None
        assert audit.event_data["suggestion_code"] == confirm_body["data"]["suggestion"]["suggestion_code"]
        assert audit.event_data["applied_schedule_code"] == schedule_code

    @pytest.mark.api
    def test_confirm_twice_fails(self, client, auth_headers, db_session):
        """重复确认返回业务错误（建议已处理）"""
        _build_topology(db_session)
        _, suggestion_id = _parse_draft(client, auth_headers)

        r1 = client.post(f"/api/ai/suggestions/{suggestion_id}/confirm", headers=auth_headers)
        assert r1.json()["code"] == 0

        r2 = client.post(f"/api/ai/suggestions/{suggestion_id}/confirm", headers=auth_headers)
        assert r2.status_code == 409
        assert r2.json()["code"] == 40901
        assert r2.json()["data"] is None

    @pytest.mark.api
    def test_confirm_not_found(self, client, auth_headers):
        """建议不存在 → 40401"""
        response = client.post(
            "/api/ai/suggestions/99999/confirm", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["code"] == 40401

    @pytest.mark.api
    def test_confirm_requires_dispatcher(self, client, manager_headers, auth_headers, db_session):
        """manager 角色不能确认建议（403）"""
        _build_topology(db_session)
        _, suggestion_id = _parse_draft(client, auth_headers)

        response = client.post(
            f"/api/ai/suggestions/{suggestion_id}/confirm", headers=manager_headers
        )
        assert response.status_code == 403
        assert response.json()["code"] == 40300


class TestRejectSuggestion:
    """拒绝建议 → 仅记录，不触发调度修改"""

    @pytest.mark.api
    def test_reject_does_not_confirm_schedule(self, client, auth_headers, db_session):
        """reject 后：建议 rejected、方案仍为 draft、审计日志"""
        _build_topology(db_session)
        body, suggestion_id = _parse_draft(client, auth_headers)
        schedule_code = body["data"]["schedule_code"]

        response = client.post(
            f"/api/ai/suggestions/{suggestion_id}/reject",
            json={"note": "权重不合理"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        reject_body = response.json()
        assert reject_body["code"] == 0
        assert reject_body["data"]["suggestion"]["status"] == "rejected"
        assert reject_body["data"]["suggestion"]["decision_note"] == "权重不合理"

        # 调度方案未被确认，仍是 draft
        gs = db_session.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        assert gs.status == "draft"

        # 审计日志
        from services.log_service import EVENT_AI_SUGGESTION_REJECT
        audit = db_session.query(LogEvent).filter(
            LogEvent.event_name == EVENT_AI_SUGGESTION_REJECT
        ).first()
        assert audit is not None
        assert audit.event_data["note"] == "权重不合理"

    @pytest.mark.api
    def test_reject_twice_fails(self, client, auth_headers, db_session):
        """重复拒绝返回业务错误"""
        _build_topology(db_session)
        _, suggestion_id = _parse_draft(client, auth_headers)

        r1 = client.post(f"/api/ai/suggestions/{suggestion_id}/reject", headers=auth_headers)
        assert r1.json()["code"] == 0

        r2 = client.post(f"/api/ai/suggestions/{suggestion_id}/reject", headers=auth_headers)
        assert r2.json()["code"] != 0


class TestListSuggestions:
    """列出 AI 建议"""

    @pytest.mark.api
    def test_list_and_filter(self, client, auth_headers, db_session):
        """列表返回建议；可按 status 过滤；非法 status 报错"""
        _build_topology(db_session)
        _, suggestion_id = _parse_draft(client, auth_headers)

        # 全部
        resp = client.get("/api/ai/suggestions", headers=auth_headers)
        assert resp.json()["code"] == 0
        items = resp.json()["data"]["items"]
        assert any(s["id"] == suggestion_id for s in items)
        assert items[0]["level"] == "suggestion"
        assert items[0]["status"] == "pending"

        # 按 pending 过滤
        resp = client.get(
            "/api/ai/suggestions?status=pending", headers=auth_headers
        )
        assert resp.json()["code"] == 0
        assert resp.json()["data"]["total"] >= 1

        # 非法 status
        resp = client.get(
            "/api/ai/suggestions?status=bogus", headers=auth_headers
        )
        assert resp.json()["code"] != 0


class TestInfoLevelSuggestion:
    """info 级别建议：无需确认直接展示，confirm 仅标记不执行"""

    @pytest.mark.api
    def test_info_confirm_marks_only(self, client, auth_headers, db_session):
        """info 级别建议 confirm → status=confirmed 且 applied_schedule_code=None（无调度修改）"""
        from services.ai_suggestion_service import create_suggestion
        from services.log_service import EVENT_AI_SUGGESTION_CONFIRM

        from models.user import User
        dispatcher = db_session.query(User).filter(User.username == "dispatcher").first()
        suggestion = create_suggestion(
            db=db_session,
            level="info",
            source="explain",
            title="方案解释",
            content="仅供展示的解释内容",
            user_id=dispatcher.id,
            role=dispatcher.role,
        )

        response = client.post(
            f"/api/ai/suggestions/{suggestion.id}/confirm", headers=auth_headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["applied_schedule_code"] is None
        assert body["data"]["suggestion"]["status"] == "confirmed"

        # 审计仍记录（无 applied_schedule_code）
        audit = db_session.query(LogEvent).filter(
            LogEvent.event_name == EVENT_AI_SUGGESTION_CONFIRM
        ).order_by(LogEvent.id.desc()).first()
        assert audit is not None
        assert audit.event_data["applied_schedule_code"] is None


class TestSuggestionEndpointAuth:
    """建议确认/拒绝端点鉴权"""

    @pytest.mark.api
    def test_get_suggestions_requires_auth(self, client):
        """未登录不能列出建议（401）"""
        response = client.get("/api/ai/suggestions")
        assert response.status_code == 401
