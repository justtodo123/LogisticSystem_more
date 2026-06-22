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
SYSTEM_PROMPT = """你是一个物流调度专家。根据用户需求和当前系统状态，生成算法参数JSON。

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
  },
  "node_dispatch": {
    "algorithm": "traditional",
    "weights": {
      "distance": 0.5,
      "time": 0.3,
      "package_count": 0.2
    }
  },
  "route_planning": {
    "algorithm": "traditional",
    "max_iterations": 1000
  }
}
```

如果用户需求不明确，使用默认参数（traditional算法，标准权重）。
"""

def build_user_prompt(user_message: str, system_context: Dict) -> str:
    """
    构建用户提示词
    
    Args:
        user_message: 用户自然语言输入
        system_context: 系统上下文（order_count, vehicle_count, node_count, pending_orders）
        
    Returns:
        完整的用户提示词
    """
    order_count = system_context.get("order_count", 0)
    vehicle_count = system_context.get("vehicle_count", 0)
    node_count = system_context.get("node_count", 0)
    pending_orders = system_context.get("pending_orders", [])
    
    # 构建订单描述（最多10个）
    orders_desc = "无待分配订单"
    if pending_orders:
        orders_desc = "\n".join([
            f"- 订单{order.order_code}: 目的地{order.destination_node_id}, 时效{order.time_window}"
            for order in pending_orders[:10]
        ])
    
    prompt = f"""当前系统状态：
- 待分配订单：{order_count}个
- 可用车辆：{vehicle_count}辆
- 节点数量：{node_count}个

订单列表（前10个）：
{orders_desc}

用户需求：{user_message}

请生成算法参数JSON。
"""
    return prompt


class DeepSeekService:
    """DeepSeek API 调用服务"""
    
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
            
            # 2. 调用 DeepSeek API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.1,  # 低温度，确保输出稳定
                    }
                )
                response.raise_for_status()
            
            # 3. 解析响应
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
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
        加载默认算法参数
        
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
            },
            "node_dispatch": {
                "algorithm": "traditional",
                "weights": {
                    "distance": 0.5,
                    "time": 0.3,
                    "package_count": 0.2
                }
            },
            "route_planning": {
                "algorithm": "traditional",
                "max_iterations": 1000
            }
        }
