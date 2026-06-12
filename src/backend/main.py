from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    code: int = 0
    message: str = "success"
    data: dict = {"status": "ok"}


# 创建FastAPI应用实例
app = FastAPI(
    title="智能物流平台",
    description="DeepSeek路径优化 - 智能物流平台后端API",
    version="0.1.0"
)

# 配置CORS中间件
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
# 支持逗号分隔的多个源，或JSON数组格式
if cors_origins_str.startswith("[") and cors_origins_str.endswith("]"):
    import json
    cors_origins = json.loads(cors_origins_str)
else:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    return HealthResponse()
