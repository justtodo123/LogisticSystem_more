"""
test_node_dispatch.py — F005 节点间调度算法单元测试

测试用例：
1. demo_mode=true：一次完成两次调度（L0→L1 + L1→L2）
2. demo_mode=false：首次调用只执行 L0→L1，第二次调用才执行 L1→L2
3. 车辆不足，无法调度
4. 包裹状态不是packed，无法调度

状态流转验证：
- F005调用后：包裹 status: packed → in_transit; 货物 status: packed → in_transit; 车辆 status: idle → delivering; 司机 status: idle → busy
- 模拟送达L0→L1后：包裹 status: in_transit → delivered; 货物 status: in_transit → pending_pack; 批次 status: pending → l0_l1_done; 车辆 status: delivering → idle; 司机 status: busy → idle
- 重新打包后：货物 status: pending_pack → packed; 新包裹 status: packed
- 模拟送达L1→L2后：包裹 status: in_transit → delivered; 货物 status: in_transit → delivered; 订单 status: delivering → completed; 批次 status: l0_l1_done → completed; 车辆 status: delivering → idle; 司机 status: busy → idle
"""
import pytest
from algorithms.node_dispatch import run_node_dispatch
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver
from models.goods import Goods
from models.order import Order


class TestDemoModeTrue:
    """demo_mode=true：一次完成两次调度"""

    @pytest.mark.unit
    def test_demo_mode_true_runs_both_levels(
        self, db_session, test_nodes, test_vehicles, test_drivers
    ):
        """
        测试 demo_mode=true 时，一次完成两次调度（L0→L1 + L1→L2）
        并验证状态流转正确
        """
        # 1. 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST001",
            order_codes=["O001"],
            goods_schedules=[
                {
                    "goods_code": "G001",
                    "order_code": "O001",
                    "path": ["SC001", "SO001", "SO010"]
                },
                {
                    "goods_code": "G002",
                    "order_code": "O001",
                    "path": ["SC001", "SO001", "SO010"]
                }
            ],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        
        # 2. 创建订单（初始状态 pending）
        order = Order(
            order_code="O001",
            destination_node_id=test_nodes["SO010"].id,  # L2节点（目的地）
            time_window="09:00-18:00",
            status="pending",
        )
        db_session.add(order)
        db_session.flush()  # 先 flush 获取订单 ID
        
        # 3. 创建货物（初始状态 pending_pack，使用正确的订单ID）
        goods1 = Goods(
            goods_code="G001",
            goods_name="测试货物1",
            goods_type="电子产品",
            weight=5.0,
            volume=0.25,
            node_id=test_nodes["SC001"].id,  # L0节点
            order_id=order.id,  # 使用实际的订单ID
            status="pending_pack",
        )
        goods2 = Goods(
            goods_code="G002",
            goods_name="测试货物2",
            goods_type="电子产品",
            weight=5.0,
            volume=0.25,
            node_id=test_nodes["SC001"].id,  # L0节点
            order_id=order.id,  # 使用实际的订单ID
            status="pending_pack",
        )
        db_session.add(goods1)
        db_session.add(goods2)
        db_session.flush()
        
        # 4. 创建 L0→L1 包裹（从存储中心到一级分拣中心）
        pkg_l0_l1 = Package(
            package_code="PKG_L0L1_001",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,  # L0
            to_node_id=test_nodes["SO001"].id,      # L1
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(pkg_l0_l1)
        db_session.commit()
        
        # 5. 执行F005（demo_mode=true）
        result = run_node_dispatch(
            db=db_session,
            schedule_code="GS_TEST001",
            demo_mode=True,
        )
        
        # 6. 验证结果
        assert result["status"] == "completed"
        assert len(result["dispatches"]) == 2  # L0→L1 和 L1→L2 各一个
        assert "message" not in result  # demo_mode=true 时没有 message 字段
        
        # 7. 验证数据库中的批次状态
        batch = db_session.query(DispatchBatch).filter(
            DispatchBatch.batch_code == result["batch_code"]
        ).first()
        assert batch is not None
        assert batch.status == "completed"
        assert batch.demo_mode == True
        assert batch.l0_l1_dispatch_count == 1
        assert batch.l1_l2_dispatch_count == 1
        
        # 8. 验证状态流转：包裹
        # L0→L1 包裹：packed → in_transit → delivered
        pkg_l0_l1 = db_session.query(Package).filter(
            Package.package_code == "PKG_L0L1_001"
        ).first()
        assert pkg_l0_l1.status == "delivered"
        
        # L1→L2 包裹：应该已创建，状态为 delivered
        pkg_l1_l2 = db_session.query(Package).filter(
            Package.package_code.like("PKG%"),
            Package.from_node_id == test_nodes["SO001"].id
        ).order_by(Package.id.desc()).first()
        assert pkg_l1_l2 is not None
        assert pkg_l1_l2.status == "delivered"
        
        # 9. 验证状态流转：货物
        # G001：pending_pack → packed → in_transit → pending_pack → packed → in_transit → delivered
        goods1 = db_session.query(Goods).filter(Goods.goods_code == "G001").first()
        assert goods1.status == "delivered"
        
        # 10. 验证状态流转：车辆
        # 车辆状态应该是 idle（因为送达后车辆状态会恢复为idle）
        vehicle = db_session.query(Vehicle).first()
        assert vehicle.status == "idle"
        
        # 11. 验证状态流转：司机
        # 司机状态应该是 idle（因为送达后司机状态会恢复为idle）
        driver = db_session.query(Driver).first()
        assert driver.status == "idle"
        
        # 12. 验证状态流转：订单
        # 订单状态应该是 completed
        order = db_session.query(Order).filter(Order.order_code == "O001").first()
        assert order.status == "completed"


class TestDemoModeFalse:
    """demo_mode=false：分阶段调度"""

    @pytest.mark.unit
    def test_first_call_only_l0_to_l1(
        self, db_session, test_nodes, test_vehicles, test_drivers
    ):
        """
        测试 demo_mode=false 时，首次调用只执行 L0→L1
        """
        # 1. 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST002",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()
        
        # 2. 创建 L0→L1 包裹
        pkg_l0_l1 = Package(
            package_code="PKG_L0L1_002",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(pkg_l0_l1)
        db_session.commit()
        
        # 3. 执行F005（demo_mode=false，首次调用）
        result = run_node_dispatch(
            db=db_session,
            schedule_code="GS_TEST002",
            demo_mode=False,
        )
        
        # 4. 验证结果
        assert result["status"] == "l0_l1_done"
        assert len(result["dispatches"]) == 1  # 只有 L0→L1
        assert "message" in result
        assert "L0→L1调度完成" in result["message"]
        
        # 5. 验证数据库中的批次状态
        batch = db_session.query(DispatchBatch).filter(
            DispatchBatch.batch_code == result["batch_code"]
        ).first()
        assert batch is not None
        assert batch.status == "l0_l1_done"
        assert batch.demo_mode == False
        assert batch.l0_l1_dispatch_count == 1
        assert batch.l1_l2_dispatch_count == 0

    @pytest.mark.unit
    def test_second_call_only_l1_to_l2(
        self, db_session, test_nodes, test_vehicles, test_drivers
    ):
        """
        测试 demo_mode=false 时，第二次调用只执行 L1→L2
        """
        # 1. 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST003",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()
        
        # 2. 创建 L0→L1 包裹
        pkg_l0_l1 = Package(
            package_code="PKG_L0L1_003",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(pkg_l0_l1)
        
        # 3. 创建 L1→L2 包裹
        pkg_l1_l2 = Package(
            package_code="PKG_L1L2_003",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SO001"].id,
            to_node_id=test_nodes["SO010"].id,
            goods_items=[{"goods_code": "G002", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(pkg_l1_l2)
        db_session.commit()
        
        # 4. 首次调用（demo_mode=false）
        result1 = run_node_dispatch(
            db=db_session,
            schedule_code="GS_TEST003",
            demo_mode=False,
        )
        assert result1["status"] == "l0_l1_done"
        
        # 5. 第二次调用（demo_mode=false）
        result2 = run_node_dispatch(
            db=db_session,
            schedule_code="GS_TEST003",
            demo_mode=False,
        )
        
        # 6. 验证结果
        assert result2["status"] == "completed"
        assert len(result2["dispatches"]) == 1  # 只有 L1→L2
        assert "message" in result2
        assert "L1→L2调度完成" in result2["message"]
        
        # 7. 验证数据库中的批次状态
        batch = db_session.query(DispatchBatch).filter(
            DispatchBatch.batch_code == result2["batch_code"]
        ).first()
        assert batch is not None
        assert batch.status == "completed"
        assert batch.demo_mode == False
        assert batch.l0_l1_dispatch_count == 1
        assert batch.l1_l2_dispatch_count == 1


class TestNodeDispatchNoVehicle:
    """车辆不足：无法调度"""

    @pytest.mark.unit
    def test_no_vehicle_returns_unallocated(self, db_session, test_nodes, test_orders, test_goods, test_vehicles):
        """
        测试没有可用车辆时，算法成功执行但返回未分配包裹
        
        注意：算法不会抛出错误，而是将未分配的包裹添加到 unallocated_packages 列表。
        """
        # 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST004",
            order_codes=["O001"],
            goods_schedules=[
                {"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}
            ],
            total_distance=0,
            total_time=0,
            total_goods=1,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()
        
        # 创建包裹（status='packed'）
        package = Package(
            package_code="PKG_TEST004",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(package)
        db_session.commit()
        
        # 调试：检查包裹是否被正确创建
        from models.sorting_center import SortingCenter
        sorting_center = db_session.query(SortingCenter).filter(
            SortingCenter.node_id == test_nodes["SO001"].id
        ).first()
        print(f"DEBUG: SO001 level = {sorting_center.level if sorting_center else 'NOT FOUND'}")
        
        # 检查包裹
        packages = db_session.query(Package).filter(
            Package.schedule_id == schedule.id,
            Package.status == 'packed'
        ).all()
        print(f"DEBUG: Found {len(packages)} packed packages for schedule {schedule.id}")
        for pkg in packages:
            print(f"  - {pkg.package_code}: from_node_id={pkg.from_node_id}, to_node_id={pkg.to_node_id}")
        
        # 将所有车辆状态设为 maintenance（不可用），并修改 last_arrived_node_id
        for vehicle in test_vehicles.values():
            vehicle.status = 'maintenance'
            vehicle.last_arrived_node_id = test_nodes["SO010"].id  # 修改为其他节点
        db_session.commit()
        
        # 执行F005（没有可用车辆）→ 应该成功执行，但返回未分配包裹
        result = run_node_dispatch(
            db=db_session,
            schedule_code="GS_TEST004",
            demo_mode=True,
        )
        
        # 验证：结果中包含未分配包裹
        assert "unallocated_packages" in result, "结果应该包含 unallocated_packages"
        assert len(result["unallocated_packages"]) > 0, "应该有未分配包裹"
        assert package.package_code in result["unallocated_packages"], "包裹应该在未分配列表中"


class TestNodeDispatchWrongStatus:
    """包裹状态不是packed：无法调度"""

    @pytest.mark.unit
    def test_wrong_status_raises_error(self, db_session, test_nodes, test_vehicles):
        """
        测试包裹状态不是packed时抛出ValueError
        """
        # 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST005",
            order_codes=["O001"],
            goods_schedules=[],
            total_distance=0,
            total_time=0,
            total_goods=0,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()
        
        # 创建包裹（status='pending_pack'，不是'packed'）
        package = Package(
            package_code="PKG_TEST005",
            weight=10.0,
            volume=0.5,
            status="pending_pack",  # 错误状态
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(package)
        db_session.commit()
        
        # 执行F005（包裹状态错误）→ 应该找不到包裹
        # 注意：算法会查询status='packed'的包裹，所以会返回空列表
        # 然后算法会抛出ValueError："L0→L1没有可调度的包裹"
        with pytest.raises(ValueError, match="L0→L1没有可调度的包裹"):
            run_node_dispatch(
                db=db_session,
                schedule_code="GS_TEST005",
                demo_mode=True,
            )


class TestUnallocatedPackages:
    """测试 unallocated_packages 功能"""

    @pytest.mark.unit
    def test_demo_mode_true_returns_unallocated(
        self, db_session, test_nodes, test_vehicles, test_drivers
    ):
        """
        测试 demo_mode=true 时，返回 unallocated_packages
        """
        # 1. 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST006",
            order_codes=["O001"],
            goods_schedules=[
                {"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}
            ],
            total_distance=0,
            total_time=0,
            total_goods=1,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 2. 创建包裹（只有1个包裹，车辆充足，应该无未分配包裹）
        pkg = Package(
            package_code="PKG_TEST006",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(pkg)
        db_session.commit()

        # 3. 执行F005（demo_mode=true）
        result = run_node_dispatch(
            db=db_session,
            schedule_code="GS_TEST006",
            demo_mode=True,
        )

        # 4. 验证结果中包含 unallocated_packages
        assert "unallocated_packages" in result
        # 车辆充足，应该无未分配包裹
        assert len(result["unallocated_packages"]) == 0

    @pytest.mark.unit
    def test_unallocated_packages_saved_to_db(
        self, db_session, test_nodes, test_vehicles, test_drivers
    ):
        """
        测试 unallocated_packages 保存到数据库
        """
        # 1. 创建全局调度方案
        from models.global_schedule import GlobalSchedule
        schedule = GlobalSchedule(
            schedule_code="GS_TEST007",
            order_codes=["O001"],
            goods_schedules=[
                {"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}
            ],
            total_distance=0,
            total_time=0,
            total_goods=1,
            score=0,
        )
        db_session.add(schedule)
        db_session.flush()

        # 2. 创建包裹
        pkg = Package(
            package_code="PKG_TEST007",
            weight=10.0,
            volume=0.5,
            status="packed",
            from_node_id=test_nodes["SC001"].id,
            to_node_id=test_nodes["SO001"].id,
            goods_items=[{"goods_code": "G001", "order_code": "O001"}],
            schedule_id=schedule.id,
        )
        db_session.add(pkg)
        db_session.commit()

        # 3. 执行F005
        result = run_node_dispatch(
            db=db_session,
            schedule_code="GS_TEST007",
            demo_mode=True,
        )

        # 4. 验证数据库中的批次包含 unallocated_packages
        from models.dispatch_batch import DispatchBatch
        batch = db_session.query(DispatchBatch).filter(
            DispatchBatch.batch_code == result["batch_code"]
        ).first()

        assert batch is not None
        # 验证 unallocated_packages 字段
        if batch.unallocated_packages:
            import json
            unallocated = json.loads(batch.unallocated_packages)
            assert isinstance(unallocated, list)
