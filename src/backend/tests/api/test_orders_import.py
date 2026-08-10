"""
订单导入增强测试（T5-1）

测试：
- 自定义列映射（column_mapping JSON）
- 错误行报告（failed_rows 指明失败行）
- skip_errors=false 时整体回滚
"""
import io
import json

import openpyxl
import pytest

from core.error_codes import CODE_ORDER_IMPORT_FAILED, CODE_PARAM_ERROR


def _build_xlsx(headers, rows):
    """内存构造 xlsx 并返回文件对象"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# 标准列（默认映射：表头即系统字段名）
STD_HEADERS = [
    "destination_node_code", "storage_center_code", "time_window",
    "goods_name", "goods_type", "weight", "volume",
]

# 中文列 + 对应映射
CN_HEADERS = ["目的地", "存储中心", "时效", "货物名称", "货物类型", "重量", "体积"]
CN_MAPPING = {
    "目的地": "destination_node_code",
    "存储中心": "storage_center_code",
    "时效": "time_window",
    "货物名称": "goods_name",
    "货物类型": "goods_type",
    "重量": "weight",
    "体积": "volume",
}


@pytest.fixture
def auth_headers(client, test_users):
    """认证头（调度员）"""
    response = client.post("/api/auth/login", json={
        "username": "dispatcher",
        "password": "123456",
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.api
@pytest.mark.phase5
class TestOrderImportEnhance:
    def test_import_basic_default_mapping(self, client, auth_headers, test_nodes):
        """默认列映射导入成功"""
        file_obj = _build_xlsx(STD_HEADERS, [
            ["SO010", "SC001", "2026-06-15 全天", "货物A", "普通", 10, 0.5],
            ["SO011", "SC001", "2026-06-15 全天", "货物B", "普通", 8, 0.4],
        ])
        response = client.post(
            "/api/orders/import",
            files={"file": ("orders.xlsx", file_obj, XLSX_MIME)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["success_count"] == 2
        assert body["data"]["failed_count"] == 0
        assert body["data"]["failed_rows"] == []

    def test_import_with_column_mapping(self, client, auth_headers, test_nodes):
        """自定义列映射：中文表头映射到系统字段"""
        file_obj = _build_xlsx(CN_HEADERS, [
            ["SO010", "SC001", "2026-06-15 全天", "货物A", "普通", 10, 0.5],
        ])
        response = client.post(
            "/api/orders/import",
            params={"column_mapping": json.dumps(CN_MAPPING)},
            files={"file": ("orders.xlsx", file_obj, XLSX_MIME)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["success_count"] == 1

    def test_import_error_rows_reported(self, client, auth_headers, test_nodes):
        """含错误行：成功行入库，failed_rows 指明失败行号"""
        file_obj = _build_xlsx(STD_HEADERS, [
            ["SO010", "SC001", "2026-06-15 全天", "货物A", "普通", 10, 0.5],  # 有效
            ["SO010", "SC001", "2026-06-15 全天", "货物B", "普通", 8, None],   # 体积为空
        ])
        response = client.post(
            "/api/orders/import",
            files={"file": ("orders.xlsx", file_obj, XLSX_MIME)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["success_count"] == 1
        assert body["data"]["failed_count"] == 1
        assert body["data"]["failed_rows"][0]["row"] == 3
        assert "必填" in body["data"]["failed_rows"][0]["error"]

    def test_import_error_all_or_nothing(self, client, auth_headers, test_nodes):
        """skip_errors=false：存在错误行则整体回滚"""
        file_obj = _build_xlsx(STD_HEADERS, [
            ["SO010", "SC001", "2026-06-15 全天", "货物A", "普通", 10, 0.5],  # 有效
            ["SO010", "SC001", "2026-06-15 全天", "货物B", "普通", 8, None],   # 体积为空
        ])
        response = client.post(
            "/api/orders/import",
            params={"skip_errors": False},
            files={"file": ("orders.xlsx", file_obj, XLSX_MIME)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == CODE_ORDER_IMPORT_FAILED
        assert body["data"]["success_count"] == 0  # 整体回滚，有效行也不入库
        assert len(body["data"]["failed_rows"]) == 1

    def test_import_invalid_column_mapping(self, client, auth_headers, test_nodes):
        """column_mapping 非法 JSON → 参数错误"""
        file_obj = _build_xlsx(STD_HEADERS, [
            ["SO010", "SC001", "2026-06-15 全天", "货物A", "普通", 10, 0.5],
        ])
        response = client.post(
            "/api/orders/import",
            params={"column_mapping": "not-json"},
            files={"file": ("orders.xlsx", file_obj, XLSX_MIME)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["code"] == CODE_PARAM_ERROR

    def test_import_skips_empty_rows(self, client, auth_headers, test_nodes):
        """空行被跳过，不影响计数"""
        file_obj = _build_xlsx(STD_HEADERS, [
            ["SO010", "SC001", "2026-06-15 全天", "货物A", "普通", 10, 0.5],
            [None, None, None, None, None, None, None],  # 空行
        ])
        response = client.post(
            "/api/orders/import",
            files={"file": ("orders.xlsx", file_obj, XLSX_MIME)},
            headers=auth_headers,
        )
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["success_count"] == 1
        assert body["data"]["failed_count"] == 0
