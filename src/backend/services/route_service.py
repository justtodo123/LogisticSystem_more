"""
路径规划服务

编排 F006 算法 → 写库的完整流程。
单事务保证原子性：routes 表写入与 F005 在同一个事务中。
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from algorithms.route_planning import run_route_planning
from models.route import Route
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.vehicle import Vehicle
from utils.response import success_response, error_response


class RouteService:
    """路径规划服务"""
    
    @staticmethod
    async def create_route_planning(
        batch_code: str,
        dispatch_codes: Optional[List[str]],
        db: Session,
    ) -> Dict[str, Any]:
        """
        编排 F006 算法 → 写库（单事务）
        
        流程：
        1. 查询 DispatchBatch (batch_code)
        2. 确定要处理的 dispatches (dispatch_codes 或批次下所有dispatch)
        3. 对每个 dispatch 调用 F006 算法 (run_route_planning(db, dispatch_id))
        4. 写入 routes 表
        
        Args:
            batch_code: 调度批次编码
            dispatch_codes: 节点调度明细编码列表（可选）
            db: 数据库会话
            
        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 查询 DispatchBatch (batch_code)
            batch = db.query(DispatchBatch).filter(
                DispatchBatch.batch_code == batch_code
            ).first()
            
            if not batch:
                return error_response(code=40001, message=f"路径规划失败：批次不存在 {batch_code}")
            
            # 2. 确定要处理的 dispatches
            if dispatch_codes:
                # 按 dispatch_codes 查询
                dispatches = db.query(NodeDispatch).filter(
                    NodeDispatch.dispatch_code.in_(dispatch_codes),
                    NodeDispatch.dispatch_batch_id == batch.id
                ).all()
            else:
                # 查询批次下所有 dispatch
                dispatches = db.query(NodeDispatch).filter(
                    NodeDispatch.dispatch_batch_id == batch.id
                ).all()
            
            if not dispatches:
                return error_response(code=40001, message="路径规划失败：没有可处理的调度明细")
            
            # 3. 对每个 dispatch 调用 F006 算法
            routes = []
            for dispatch in dispatches:
                # 调用 F006 算法
                route_data = run_route_planning(db, dispatch.id)
                
                # 4. 写入 routes 表
                route = Route(
                    route_code=route_data["route_code"],
                    dispatch_id=route_data["dispatch_id"],
                    vehicle_id=route_data["vehicle_id"],
                    route_segments=route_data["route_segments"],
                    total_distance=route_data["total_distance"],
                    total_time=route_data["total_time"],
                    total_emission=route_data["total_emission"],
                    algorithm_type=route_data["algorithm_type"]
                )
                db.add(route)
                routes.append(route_data)
            
            # 添加提交逻辑
            db.commit()
            
            # 5. 构建响应（移除内部 id，仅暴露 _code 业务编号）
            api_routes = []
            for r in routes:
                api_routes.append({
                    "route_code": r["route_code"],
                    "dispatch_code": r["dispatch_code"],
                    "vehicle_code": r["vehicle_code"],
                    "route_segments": r["route_segments"],
                    "total_distance": r["total_distance"],
                    "total_time": r["total_time"],
                    "total_emission": r["total_emission"],
                    "algorithm_type": r["algorithm_type"],
                })
            return success_response(data={
                "batch_code": batch_code,
                "status": batch.status,
                "routes": api_routes
            })
            
        except Exception as e:
            # 不在这里调用 db.rollback()，由调用者处理
            return error_response(code=40001, message=f"路径规划失败：{str(e)}")
    
    @staticmethod
    async def get_routes(
        batch_code: Optional[str],
        vehicle_code: Optional[str],
        page: int,
        page_size: int,
        db: Session,
    ) -> Dict[str, Any]:
        """
        查询路线列表
        
        流程：
        1. 构建查询（关联 DispatchBatch 获取 batch_code）
        2. 按 batch_code 筛选（可选）
        3. 按 vehicle_code 筛选（可选，需JOIN vehicles表）
        4. 分页查询
        5. 返回成功响应
        
        Args:
            batch_code: 批次编码（可选）
            vehicle_code: 车辆编码（可选）
            page: 页码
            page_size: 每页数量
            db: 数据库会话
            
        Returns:
            统一响应格式 dict
        """
        # 1. 构建查询
        query = db.query(Route).join(NodeDispatch, Route.dispatch_id == NodeDispatch.id)
        
        # 2. 按 batch_code 筛选（可选）
        if batch_code:
            query = query.join(DispatchBatch, NodeDispatch.dispatch_batch_id == DispatchBatch.id)
            query = query.filter(DispatchBatch.batch_code == batch_code)
        
        # 3. 按 vehicle_code 筛选（可选，需JOIN vehicles表）
        if vehicle_code:
            query = query.join(Vehicle, Route.vehicle_id == Vehicle.id)
            query = query.filter(Vehicle.vehicle_code == vehicle_code)
        
        # 4. 分页查询
        total = query.count()
        routes = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 5. 构建响应
        items = []
        for route in routes:
            # 获取 batch_code
            dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == route.dispatch_id).first()
            batch_code_value = None
            if dispatch:
                batch = db.query(DispatchBatch).filter(DispatchBatch.id == dispatch.dispatch_batch_id).first()
                if batch:
                    batch_code_value = batch.batch_code
            
            # 获取 dispatch_code
            dispatch_code_value = dispatch.dispatch_code if dispatch else None
            
            # 获取 vehicle_code
            vehicle = db.query(Vehicle).filter(Vehicle.id == route.vehicle_id).first()
            vehicle_code_value = vehicle.vehicle_code if vehicle else None
            
            items.append({
                "route_code": route.route_code,
                "batch_code": batch_code_value,
                "dispatch_code": dispatch_code_value,
                "vehicle_code": vehicle_code_value,
                "total_distance": float(route.total_distance),
                "total_time": float(route.total_time),
                "total_emission": float(route.total_emission),
                "created_at": route.created_at.isoformat() if route.created_at else None
            })
        
        return success_response(data={
            "items": items,
            "total": total
        })
    
    @staticmethod
    async def get_route_detail(
        route_code: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        查询路线详情
        
        流程：
        1. 查询 Route (route_code)
        2. 如果不存在，返回404错误
        3. 构建响应（包含 route_segments）
        4. 返回成功响应
        
        Args:
            route_code: 路线编码
            db: 数据库会话
            
        Returns:
            统一响应格式 dict
        """
        # 1. 查询 Route (route_code)
        route = db.query(Route).filter(Route.route_code == route_code).first()
        
        # 2. 如果不存在，返回404错误
        if not route:
            return error_response(code=40400, message=f"路线不存在：{route_code}")
        
        # 3. 构建响应（包含 route_segments）
        # 获取 batch_code
        dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == route.dispatch_id).first()
        batch_code_value = None
        if dispatch:
            batch = db.query(DispatchBatch).filter(DispatchBatch.id == dispatch.dispatch_batch_id).first()
            if batch:
                batch_code_value = batch.batch_code
        
        # 获取 dispatch_code
        dispatch_code_value = dispatch.dispatch_code if dispatch else None
        
        # 获取 vehicle_code
        vehicle = db.query(Vehicle).filter(Vehicle.id == route.vehicle_id).first()
        vehicle_code_value = vehicle.vehicle_code if vehicle else None
        
        return success_response(data={
            "route_code": route.route_code,
            "batch_code": batch_code_value,
            "dispatch_code": dispatch_code_value,
            "vehicle_code": vehicle_code_value,
            "route_segments": route.route_segments,
            "total_distance": float(route.total_distance),
            "total_time": float(route.total_time),
            "total_emission": float(route.total_emission),
            "algorithm_type": route.algorithm_type,
            "created_at": route.created_at.isoformat() if route.created_at else None
        })
    
    @staticmethod
    async def get_route_coordinates(
        vehicle_code: str,
        batch_code: Optional[str],
        db: Session,
    ) -> Dict[str, Any]:
        """
        查询车辆路线坐标（供前端可视化）
        
        流程：
        1. 查询 Vehicle (vehicle_code)
        2. 如果不存在，返回404错误
        3. 查询该车辆的所有 Route（可按 batch_code 筛选）
        4. 构建响应（每个 Route 包含 coordinates 数组）
        5. 返回成功响应
        
        Args:
            vehicle_code: 车辆编码
            batch_code: 批次编码（可选）
            db: 数据库会话
            
        Returns:
            统一响应格式 dict
        """
        # 1. 查询 Vehicle (vehicle_code)
        vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
        
        # 2. 如果不存在，返回404错误
        if not vehicle:
            return error_response(code=40400, message=f"车辆不存在：{vehicle_code}")
        
        # 3. 查询该车辆的所有 Route（可按 batch_code 筛选）
        query = db.query(Route).filter(Route.vehicle_id == vehicle.id)
        
        if batch_code:
            # 需要JOIN node_dispatches和dispatch_batches来按batch_code筛选
            query = query.join(NodeDispatch, Route.dispatch_id == NodeDispatch.id)
            query = query.join(DispatchBatch, NodeDispatch.dispatch_batch_id == DispatchBatch.id)
            query = query.filter(DispatchBatch.batch_code == batch_code)
        
        routes = query.all()
        
        # 4. 构建响应（每个 Route 包含 coordinates 数组）
        route_list = []
        for route in routes:
            # 从 route_segments 中提取 coordinates
            coordinates = []
            for segment in route.route_segments:
                # 添加起点坐标
                coordinates.append([segment["start_lng"], segment["start_lat"]])
                # 添加终点坐标（如果是最后一个segment）
                if segment == route.route_segments[-1]:
                    coordinates.append([segment["end_lng"], segment["end_lat"]])
            
            # 获取 batch_code
            dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == route.dispatch_id).first()
            batch_code_value = None
            if dispatch:
                batch = db.query(DispatchBatch).filter(DispatchBatch.id == dispatch.dispatch_batch_id).first()
                if batch:
                    batch_code_value = batch.batch_code
            
            route_list.append({
                "route_code": route.route_code,
                "batch_code": batch_code_value,
                "coordinates": coordinates,
                "total_distance": float(route.total_distance)
            })
        
        # 5. 返回成功响应
        return success_response(data={
            "vehicle_code": vehicle_code,
            "routes": route_list
        })
