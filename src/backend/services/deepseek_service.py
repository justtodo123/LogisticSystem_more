"""
DeepSeek API 调用服务

功能：
1. 调用 DeepSeek API 解析自然语言
2. 将自然语言转为算法参数 JSON
3. 处理 API 调用失败场景（降级）
"""
import json
import logging
from typing import Any, Dict, Optional

import httpx

from config.database import settings

logger = logging.getLogger(__name__)

# DeepSeek 提示词模板
SYSTEM_PROMPT = """你是一个物流调度专家。根据用户需求和当前系统状态，生成全局调度算法参数JSON。

你必须严格按照以下JSON格式输出，不要输出任何其他内容：

```json
{
  "global_schedule": {
    "algorithm": "traditional",
    "weights": {
      "distance": 0.5,
      "time": 0.3,
      "package_count": 0.2
    }
  }
}
```

权重说明（global_schedule 模块）：
- distance: 距离权重（越大越倾向缩短总距离）
- time: 时间权重（越大越倾向缩短总时间）
- package_count: 包裹数权重（越大越倾向减少包裹数/合并包裹）
- 三个权重之和应为 1.0（如 0.5+0.3+0.2=1.0）

注意：
- node_dispatch 和 route_planning 模块使用系统默认参数，不通过AI覆盖。
- 你只需返回 global_schedule 部分的参数。

如果提供了历史参考方案：
- 分析各方案的评分优劣，找出表现最好的方案的权重特征
- 如果用户说"参考方案X"，应优先对齐方案X的权重倾向
- 如果方案X是重规划版本且评分更优，应朝其优化方向调整权重

如果是重规划目标方案：
- 分析当前方案的不足（距离/时间/包裹数哪项拖后腿）
- 生成能针对性改善目标方案的 global_schedule 优化参数

如果用户需求不明确，使用默认参数（traditional算法，标准权重）。
"""

def build_user_prompt(user_message: str, system_context: Dict) -> str:
    """
    构建用户提示词
    
    Args:
        user_message: 用户自然语言输入
        system_context: 系统上下文，可包含：
            - order_count, vehicle_count, node_count, pending_orders（基础上下文）
            - reference_schedules: 参考方案列表 [{"schedule_code": "GS001", "total_distance": 120.5, ...}]
            - target_schedule: 目标方案（重规划场景）{"schedule_code": "GS001", ...}
        
    Returns:
        完整的用户提示词
    """
    order_count = system_context.get("order_count", 0)
    vehicle_count = system_context.get("vehicle_count", 0)
    node_count = system_context.get("node_count", 0)
    pending_orders = system_context.get("pending_orders", [])
    
    # 构建订单描述（最多10个）
    # 注意：pending_orders 来自 API 响应 items，是 dict 而非 ORM 对象
    orders_desc = "无待分配订单"
    if pending_orders:
        orders_desc = "\n".join([
            f"- 订单{o.get('order_code', '?')}: "
            f"目的地{o.get('destination_node_code', o.get('destination_node_id', '?'))}, "
            f"时效{o.get('time_window', '?')}"
            for o in pending_orders[:10]
        ])
    
    # 构建参考方案描述
    reference_text = ""
    reference_schedules = system_context.get("reference_schedules", [])
    if reference_schedules:
        lines = ["\n历史参考方案（请分析其表现并优化参数）："]
        for s in reference_schedules:
            replan_tag = f" [重规划·{s.get('replan_reason', '未知')}]" if s.get("is_replan") else ""
            lines.append(
                f"- {s['schedule_code']} v{s.get('version', 1)}{replan_tag}: "
                f"总距离{s.get('total_distance', '?')}km, "
                f"总时间{s.get('total_time', '?')}h, "
                f"货物数{s.get('total_goods', '?')}件, "
                f"评分{s.get('score', '?')}"
            )
        reference_text = "\n".join(lines)
    
    # 构建目标方案描述（重规划场景）
    target_text = ""
    target_schedule = system_context.get("target_schedule")
    if target_schedule:
        target_text = f"""
重规划目标方案：
- 编码: {target_schedule.get('schedule_code', '?')}
- 当前指标: 总距离{target_schedule.get('total_distance', '?')}km, 总时间{target_schedule.get('total_time', '?')}h
- 货物数: {target_schedule.get('total_goods', '?')}件, 评分: {target_schedule.get('score', '?')}
- 原算法类型: {target_schedule.get('algorithm_type', 'traditional')}
注意：新生成的参数将用于此方案的版本化重规划，请生成能改善目标方案的优化参数。
"""
    
    prompt = f"""当前系统状态：
- 待分配订单：{order_count}个
- 可用车辆：{vehicle_count}辆
- 节点数量：{node_count}个

订单列表（前10个）：
{orders_desc}
{reference_text}{target_text}
用户需求：{user_message}

请生成算法参数JSON。
"""
    return prompt


class DeepSeekService:
    """DeepSeek API 调用服务（统一 OpenAI /chat/completions 格式，兼容官方 & 火山引擎）"""

    @staticmethod
    def _build_request_body(user_prompt: str, system_prompt: Optional[str] = None) -> Dict:
        """
        构建请求体 — 统一使用 OpenAI /chat/completions 格式
        
        火山引擎 ARK 和 DeepSeek 官方均兼容此格式，响应结构稳定可预测：
            {"model": "...", "messages": [{"role":"system",...}, {"role":"user",...}], "temperature":0.1}
        
        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词（可选，默认使用SYSTEM_PROMPT）
        """
        return {
            "model": settings.DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt if system_prompt else SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
        }

    @staticmethod
    def _extract_response_content(result: Dict) -> str:
        """
        解析响应内容 — 统一 OpenAI /chat/completions 格式

        result["choices"][0]["message"]["content"]
        """
        return result["choices"][0]["message"]["content"]

    @staticmethod
    def _build_api_url() -> str:
        """构建完整的 API 端点 URL — 统一 /chat/completions"""
        base = settings.DEEPSEEK_API_BASE.rstrip("/")
        return f"{base}/chat/completions"
    
    @staticmethod
    async def parse_natural_language(user_message: str, system_context: Dict) -> Dict:
        """
        解析自然语言，生成算法参数
        
        Args:
            user_message: 用户自然语言输入
            system_context: 系统上下文（order_count, vehicle_count等）
            
        Returns:
            {
                "success": bool,
                "algorithm_params": Dict,  # 成功时返回
                "raw_response": str,         # DeepSeek原始响应
                "error": str                 # 失败时返回
            }
        """
        # 检查 API Key 是否配置
        if not settings.DEEPSEEK_API_KEY:
            logger.warning("DeepSeek API Key 未配置，使用默认参数")
            return {
                "success": False,
                "error": "DeepSeek API Key 未配置",
                "algorithm_params": DeepSeekService._load_default_params()
            }
        
        try:
            # 1. 构建提示词
            user_prompt = build_user_prompt(user_message, system_context)
            
            # 2. 调用 API（自动适配 OpenAI / 火山引擎 格式）
            request_body = DeepSeekService._build_request_body(user_prompt)
            api_url = DeepSeekService._build_api_url()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )
                response.raise_for_status()

            # 3. 解析响应
            result = response.json()
            content = DeepSeekService._extract_response_content(result)
            
            # 4. 提取 JSON（可能包含在```json ```中）
            algorithm_params = DeepSeekService._extract_json(content)
            
            logger.info(f"DeepSeek API 调用成功，算法参数：{algorithm_params}")
            
            return {
                "success": True,
                "algorithm_params": algorithm_params,
                "raw_response": content
            }
            
        except httpx.TimeoutException:
            logger.error("DeepSeek API 调用超时（30秒）")
            return {
                "success": False,
                "error": "DeepSeek API 调用超时（30秒）",
                "algorithm_params": DeepSeekService._load_default_params()
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API 返回错误：{e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"DeepSeek API 返回错误：{e.response.status_code}",
                "algorithm_params": DeepSeekService._load_default_params()
            }
        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek 返回格式错误，无法解析 JSON：{e}")
            return {
                "success": False,
                "error": "DeepSeek 返回格式错误，无法解析 JSON",
                "algorithm_params": DeepSeekService._load_default_params()
            }
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败：{str(e)}")
            return {
                "success": False,
                "error": f"DeepSeek API 调用失败：{str(e)}",
                "algorithm_params": DeepSeekService._load_default_params()
            }
    
    @staticmethod
    def _extract_json(content: str) -> Dict:
        """
        从 DeepSeek 返回内容中提取 JSON
        
        Args:
            content: DeepSeek 返回的内容
            
        Returns:
            解析后的 JSON 字典
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试从 ```json ``` 中提取
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            json_str = content[start:end].strip()
            return json.loads(json_str)
        
        # 尝试从 ``` 中提取
        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            json_str = content[start:end].strip()
            return json.loads(json_str)
        
        raise json.JSONDecodeError("无法从内容中提取 JSON", content, 0)
    
    @staticmethod
    def _load_default_params() -> Dict:
        """
        加载默认算法参数（只含 global_schedule，node_dispatch/route_planning 使用系统默认值）
        
        Returns:
            默认算法参数字典
        """
        return {
            "global_schedule": {
                "algorithm": "traditional",
                "weights": {
                    "distance": 0.5,
                    "time": 0.3,
                    "package_count": 0.2
                }
            }
        }

    @staticmethod
    async def explain_schedule(schedule_data: Dict[str, Any], batch_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成调度方案解释（F015）
        
        Args:
            schedule_data: 调度方案数据字典
            batch_data: 批次数据字典（可选）
        
        Returns:
            包含explanation、key_decisions、potential_risks、suggestions的字典
        """
        # 1. 构建系统提示词
        system_prompt = """你是一个物流调度专家，擅长解释调度决策逻辑。请根据提供的调度方案数据，生成清晰、详细的解释。

输出格式要求（严格JSON格式）：
{
  "explanation": "字符串，整体解释文本",
  "key_decisions": ["字符串数组，关键决策列表"],
  "potential_risks": ["字符串数组，潜在风险列表"],
  "suggestions": ["字符串数组，优化建议列表"]
}

注意：
1. 解释应该清晰易懂，避免使用过于专业的术语
2. 关键决策应该具体、可操作
3. 潜在风险应该实际、可预防
4. 优化建议应该具体、可执行"""

        # 2. 构建用户提示词（压缩数据，避免 token 过多导致超时）
        goods_schedules = schedule_data.get('goods_schedules', [])
        packages = schedule_data.get('packages', [])

        # 货物路径摘要：每条货物只保留 goods_code + path 节点序列
        goods_summary = []
        for gs in goods_schedules:
            path = gs.get('path', [])
            # path 可能是字符串列表 ["SC001","SO001"] 或对象列表 [{"node_code":"SC001",...}]
            node_codes = []
            for p in path:
                if isinstance(p, dict):
                    node_codes.append(p.get('node_code', '?'))
                else:
                    node_codes.append(str(p))
            goods_summary.append(f"{gs.get('goods_code','?')}: {' → '.join(node_codes)}")
        goods_text = "\n".join(goods_summary[:30])  # 最多展示 30 条
        if len(goods_summary) > 30:
            goods_text += f"\n...（共 {len(goods_summary)} 条，已截断）"

        # 包裹摘要：只保留包裹编码 + 状态
        pkg_summary = []
        for p in packages:
            goods_list = [g.get('goods_code','?') for g in p.get('goods_items',[])]
            pkg_summary.append(f"{p.get('package_code','?')}[{p.get('status','?')}]: {', '.join(goods_list[:5])}")
        packages_text = "\n".join(pkg_summary[:20])  # 最多展示 20 个包裹
        if len(pkg_summary) > 20:
            packages_text += f"\n...（共 {len(pkg_summary)} 个包裹，已截断）"

        user_prompt = f"""请解释以下调度方案：

调度方案编码: {schedule_data.get('schedule_code', '?')}
总距离: {schedule_data.get('total_distance', '?')} km
总时间: {schedule_data.get('total_time', '?')} 小时
总货物数: {schedule_data.get('total_goods', '?')}
评分: {schedule_data.get('score', '?')}
算法类型: {schedule_data.get('algorithm_type', '?')}
创建时间: {schedule_data.get('created_at', '?')}

货物路径清单:
{goods_text if goods_text else '（无数据）'}

包裹清单:
{packages_text if packages_text else '（无数据）'}

请生成解释。"""

        # 3. 调用DeepSeek API
        try:
            request_body = DeepSeekService._build_request_body(user_prompt, system_prompt)
            api_url = DeepSeekService._build_api_url()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )
                response.raise_for_status()
            
            # 4. 解析响应
            result = response.json()
            content = DeepSeekService._extract_response_content(result)
            explanation_data = DeepSeekService._extract_json(content)
            
            # 5. 验证结果格式
            if not isinstance(explanation_data, dict) or 'explanation' not in explanation_data:
                raise ValueError("Invalid response format")
            
            logger.info(f"DeepSeek API 调用成功，生成方案解释")
            return explanation_data
            
        except httpx.TimeoutException:
            logger.error("DeepSeek API 调用超时（30秒）")
            return {
                "explanation": "AI服务暂时不可用，请稍后重试",
                "key_decisions": [],
                "potential_risks": [],
                "suggestions": []
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API 返回错误：{e.response.status_code} - {e.response.text}")
            return {
                "explanation": "AI服务暂时不可用，请稍后重试",
                "key_decisions": [],
                "potential_risks": [],
                "suggestions": []
            }
        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek 返回格式错误，无法解析 JSON：{e}")
            return {
                "explanation": "AI服务暂时不可用，请稍后重试",
                "key_decisions": [],
                "potential_risks": [],
                "suggestions": []
            }
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败：{str(e)}")
            return {
                "explanation": "AI服务暂时不可用，请稍后重试",
                "key_decisions": [],
                "potential_risks": [],
                "suggestions": []
            }

    @staticmethod
    async def review_schedule(schedule_data: Dict[str, Any], batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成调度方案审查报告（F016）
        
        Args:
            schedule_data: 调度方案数据字典
            batch_data: 批次数据字典
        
        Returns:
            包含risks的字典
        """
        # 1. 构建系统提示词
        system_prompt = """你是一个物流调度审查专家，擅长识别潜在风险。请根据提供的调度方案和批次数据，识别所有潜在风险，并给出优化建议。

输出格式要求（严格JSON格式）：
{
  "risks": [
    {
      "type": "风险类型（road/package/node/vehicle/route）",
      "description": "风险描述",
      "severity": "严重级别（high/medium/low）",
      "suggestion": "优化建议"
    }
  ]
}

风险类型说明（参考阶段7异常类型）：
- `road`: 道路风险（如拥堵、道路封闭）→ 对应异常类型 `road`
- `package`: 包裹风险（如损坏、丢失）→ 对应异常类型 `package`
- `node`: 节点风险（如容量不足、维修）→ 对应异常类型 `node`
- `vehicle`: 车辆风险（如超载、故障）→ 对应目标类型 `vehicle`
- `route`: 路线风险（如超时、碳排放超标）→ 对应目标类型 `route`

严重级别说明：
- `high`: 高风险（需要立即处理，如超载超过20%、超时超过2小时）
- `medium`: 中风险（需要关注，如超载超过10%、超时超过1小时）
- `low`: 低风险（可以忽略，如超载低于10%、超时低于1小时）

注意：
1. 风险类型应该与阶段7的异常类型保持一致
2. 风险描述应该详细、可理解
3. 严重级别应该根据实际数据计算（如超载百分比、超时时间）
4. 优化建议应该可行、可操作（如更换车辆、调整路线）
"""

        # 2. 构建用户提示词（压缩数据，避免 token 过多导致超时）
        dispatches = batch_data.get('dispatches', [])
        routes = batch_data.get('routes', [])

        # 车辆调度摘要
        disp_summary = []
        for d in dispatches[:15]:
            tasks = d.get('tasks', [])
            task_nodes = []
            for t in tasks[:3]:
                task_nodes.append(f"{t.get('from_node_code','?')}→{t.get('to_node_code','?')}")
            disp_summary.append(f"{d.get('dispatch_code','?')} veh:{d.get('vehicle_code','?')} tasks:{'; '.join(task_nodes)}")
        dispatches_text = "\n".join(disp_summary)
        if len(dispatches) > 15:
            dispatches_text += f"\n...（共 {len(dispatches)} 条调度，已截断）"

        # 路线摘要
        route_summary = []
        for r in routes[:15]:
            route_summary.append(f"{r.get('route_code','?')} veh:{r.get('vehicle_code','?')} dist:{r.get('total_distance','?')}km time:{r.get('total_time','?')}h")
        routes_text = "\n".join(route_summary)
        if len(routes) > 15:
            routes_text += f"\n...（共 {len(routes)} 条路线，已截断）"

        user_prompt = f"""请审查以下调度方案和批次：

调度方案编码: {schedule_data.get('schedule_code', '?')}
总距离: {schedule_data.get('total_distance', '?')} km
总时间: {schedule_data.get('total_time', '?')} 小时
总货物数: {schedule_data.get('total_goods', '?')}
评分: {schedule_data.get('score', '?')}

批次编码: {batch_data.get('batch_code', '?')}
状态: {batch_data.get('status', '?')}
L0→L1调度次数: {batch_data.get('l0_l1_dispatch_count', '?')}
L1→L2调度次数: {batch_data.get('l1_l2_dispatch_count', '?')}

车辆调度清单:
{dispatches_text if dispatches_text else '（无数据）'}

路线清单:
{routes_text if routes_text else '（无数据）'}

请识别潜在风险。
"""

        # 3. 调用DeepSeek API
        try:
            request_body = DeepSeekService._build_request_body(user_prompt, system_prompt)
            api_url = DeepSeekService._build_api_url()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )
                response.raise_for_status()
            
            # 4. 解析响应
            result = response.json()
            content = DeepSeekService._extract_response_content(result)
            review_data = DeepSeekService._extract_json(content)
            
            # 5. 验证结果格式
            if not isinstance(review_data, dict) or 'risks' not in review_data:
                raise ValueError("Invalid response format")
            
            logger.info(f"DeepSeek API 调用成功，生成方案审查报告")
            return review_data
            
        except httpx.TimeoutException:
            logger.error("DeepSeek API 调用超时（30秒）")
            return {"risks": []}
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API 返回错误：{e.response.status_code} - {e.response.text}")
            return {"risks": []}
        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek 返回格式错误，无法解析 JSON：{e}")
            return {"risks": []}
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败：{str(e)}")
            return {"risks": []}

    @staticmethod
    async def analyze_exception(exception_data: Dict[str, Any], schedule_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成异常事件分析建议（F017）
        
        Args:
            exception_data: 异常事件数据字典
            schedule_data: 调度方案数据字典（可选）
        
        Returns:
            包含root_cause、suggestions、auto_fix_available的字典
        """
        # 1. 构建系统提示词
        system_prompt = """你是一个物流异常处理专家，擅长分析异常原因并给出调整建议。请根据提供的异常事件数据，分析根本原因，并给出具体、可操作的处理建议。

输出格式要求（严格JSON格式）：
{
  "root_cause": "字符串，根本原因（简明扼要）",
  "suggestions": [
    "字符串，建议1（具体、可操作，如'建议将包裹C重新分配给车辆D，因为...'）",
    "字符串，建议2"
  ],
  "auto_fix_available": 布尔值，是否可自动修复（如是否需要重新调度）
}

分析原则：
1. 根本原因应该准确、有依据（基于异常类型、子类型、目标类型）
2. 建议应该具体、可操作（避免"建议优化路线"这种模糊建议，应该给出具体方案）
3. 建议应该参考PRD中的示例格式（如"建议将包裹C重新分配给车辆D，因为..."）
4. auto_fix_available应该根据实际情况判断：
   - 如果推荐操作是`reroute`（重路径规划），通常可以自动修复（auto_fix_available=true）
   - 如果推荐操作是`redispatch`（重调度），通常需要人工确认（auto_fix_available=false）
   - 如果异常类型是`node`（节点异常），通常需要人工确认（auto_fix_available=false）

示例建议格式：
- 道路异常："建议将包裹C重新分配给车辆D，因为车辆D当前路线不经过异常道路"
- 包裹异常："建议将损坏的包裹C重新打包，使用新的包裹编码PKG999"
- 节点异常："建议将L1分拣中心从SC001更换为SC002，因为SC001容量不足"
"""

        # 2. 构建用户提示词（压缩数据，避免 token 过多导致超时）
        if schedule_data:
            gs_list = schedule_data.get('goods_schedules', [])
            schedule_summary = f"方案{schedule_data.get('schedule_code','?')}: 距离{schedule_data.get('total_distance','?')}km 时间{schedule_data.get('total_time','?')}h 货物{len(gs_list)}件 评分{schedule_data.get('score','?')}"
            if gs_list:
                paths = []
                for gs in gs_list[:10]:
                    node_codes = []
                    for p in gs.get('path', []):
                        if isinstance(p, dict):
                            node_codes.append(p.get('node_code', '?'))
                        else:
                            node_codes.append(str(p))
                    paths.append(f"{gs.get('goods_code','?')}: {' → '.join(node_codes)}")
                schedule_summary += "\n货物路径:\n" + "\n".join(paths)
                if len(gs_list) > 10:
                    schedule_summary += f"\n...（共 {len(gs_list)} 条，已截断）"
        else:
            schedule_summary = "无关联调度方案"

        user_prompt = f"""请分析以下异常事件，并给出处理建议：

## 异常事件详情
- 异常事件编码: {exception_data.get('event_code', '?')}
- 异常类型: {exception_data.get('exception_type', '?')} (road/package/node)
- 异常子类型: {exception_data.get('exception_subtype', '?')} (congestion/damage/capacity_limit/...)
- 目标类型: {exception_data.get('target_type', '?')} (node/package/route/vehicle)
- 目标编码: {exception_data.get('target_code', '?')}
- 描述: {exception_data.get('description', '?')}
- 推荐操作: {exception_data.get('recommended_action', '?')} (redispatch/reroute)
- 创建时间: {exception_data.get('created_at', '?')}

## 关联调度方案
{schedule_summary}

## 当前状态
- 异常事件状态: {exception_data.get('status', '?')}

请根据以上信息，分析根本原因，并给出具体、可操作的处理建议。
"""

        # 3. 调用DeepSeek API
        try:
            request_body = DeepSeekService._build_request_body(user_prompt, system_prompt)
            api_url = DeepSeekService._build_api_url()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )
                response.raise_for_status()
            
            # 4. 解析响应
            result = response.json()
            content = DeepSeekService._extract_response_content(result)
            analysis_data = DeepSeekService._extract_json(content)
            
            # 5. 验证结果格式
            if not isinstance(analysis_data, dict) or 'root_cause' not in analysis_data:
                raise ValueError("Invalid response format")
            
            logger.info(f"DeepSeek API 调用成功，生成异常分析建议")
            return analysis_data
            
        except httpx.TimeoutException:
            logger.error("DeepSeek API 调用超时（30秒）")
            return {
                "root_cause": "AI服务暂时不可用，请稍后重试",
                "suggestions": [],
                "auto_fix_available": False
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API 返回错误：{e.response.status_code} - {e.response.text}")
            return {
                "root_cause": "AI服务暂时不可用，请稍后重试",
                "suggestions": [],
                "auto_fix_available": False
            }
        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek 返回格式错误，无法解析 JSON：{e}")
            return {
                "root_cause": "AI服务暂时不可用，请稍后重试",
                "suggestions": [],
                "auto_fix_available": False
            }
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败：{str(e)}")
            return {
                "root_cause": "AI服务暂时不可用，请稍后重试",
                "suggestions": [],
                "auto_fix_available": False
            }
