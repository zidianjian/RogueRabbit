"""
FastAPI REST 应用 - 物品管理 API

提供简单的 CRUD 操作，用于演示 LLM 通过 MCP 调用 REST API。
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# 创建 logger 引用
logger = logging.getLogger("rest-api")

# ========================================
# 日志配置
# ========================================

# 配置日志输出到 stderr（避免干扰 STDIO 通信）
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("rest-api")

# ========================================
# 数据模型
# ========================================


class ItemBase(BaseModel):
    """物品基础模型"""

    name: str
    price: float
    quantity: int = 0


class Item(ItemBase):
    """物品完整模型（包含 ID）"""

    id: int


class ItemCreate(ItemBase):
    """创建物品的请求模型"""

    pass


# ========================================
# 内存数据库
# ========================================

_items_db: dict[int, dict] = {}
_item_id_counter = 0


def _init_sample_data():
    """初始化示例数据"""
    global _item_id_counter
    _items_db[1] = {"id": 1, "name": "Apple", "price": 1.5, "quantity": 100}
    _items_db[2] = {"id": 2, "name": "Banana", "price": 2.0, "quantity": 50}
    _items_db[3] = {"id": 3, "name": "Orange", "price": 3.0, "quantity": 75}
    _item_id_counter = 4
    logger.info(f"初始化示例数据完成，共 {len(_items_db)} 个物品")


# ========================================
# 应用生命周期
# ========================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据
    logger.info("=" * 50)
    logger.info("RogueRabbit REST API 启动中...")
    logger.info("=" * 50)
    _init_sample_data()
    yield
    # 关闭时清理
    _items_db.clear()
    logger.info("REST API 服务已关闭")


# ========================================
# FastAPI 应用
# ========================================

app = FastAPI(
    title="RogueRabbit REST API",
    description="简单的物品管理 API，用于演示 LLM + MCP 集成",
    version="0.2.1",
    lifespan=lifespan,
)


# ========================================
# 请求日志中间件
# ========================================


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求"""
    logger.info(f">>> {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"<<< {request.method} {request.url.path} -> {response.status_code}")
    return response


# ========================================
# API 路由
# ========================================


@app.get("/")
async def root():
    """根路径"""
    return {"message": "RogueRabbit REST API", "version": "0.2.1"}


@app.get("/items/", response_model=list[Item])
async def list_items():
    """获取所有物品列表"""
    return list(_items_db.values())


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """获取单个物品详情"""
    if item_id not in _items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return _items_db[item_id]


@app.post("/items/", response_model=Item)
async def create_item(item: ItemCreate):
    """创建新物品"""
    global _item_id_counter
    new_item = {"id": _item_id_counter, **item.model_dump()}
    _items_db[_item_id_counter] = new_item
    _item_id_counter += 1
    return new_item


@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemCreate):
    """更新物品信息"""
    if item_id not in _items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    updated_item = {"id": item_id, **item.model_dump()}
    _items_db[item_id] = updated_item
    return updated_item


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """删除物品"""
    if item_id not in _items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del _items_db[item_id]
    return {"message": f"Item {item_id} deleted"}


# ========================================
# 入口
# ========================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 50)
    print("RogueRabbit REST API")
    print("=" * 50)
    print("启动方式:")
    print("  直接运行: python -m rogue_rabbit.apps.rest.app")
    print("  或使用:   uvicorn rogue_rabbit.apps.rest.app:app --reload")
    print("=" * 50 + "\n")

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
