"""
DeepSeek API 调用服务

功能：
1. 调用 DeepSeek API 解析自然语言
2. 将自然语言转为算法参数 JSON
3. 处理 API 调用失败场景（降级）
"""
import json
import logging
from typing import Dict, Optional

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
    def _build_request_body(user_prompt: str) -> Dict:
        """
        构建请求体 — 统一使用 OpenAI /chat/completions 格式

        火山引擎 ARK 和 DeepSeek 官方均兼容此格式，响应结构稳定可预测：
            {"model": "...", "messages": [{"role":"system",...}, {"role":"user",...}], "temperature":0.1}
        """
        return {
            "model": settings.DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
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

            async with httpx.AsyncClient(timeout=30.0) as client:
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
