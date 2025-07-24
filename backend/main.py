"""
FastAPI后端服务 - 项目管理系统
提供RESTful API接口供Flutter前端调用
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import json
import os
import time
import datetime
import uuid
from contextlib import contextmanager

app = FastAPI(title="Project Management API", version="1.0.0")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库路径
DB_DIR = "data"
DB_LEARN = os.path.join(DB_DIR, "learn.db")
DB_REVIEW = os.path.join(DB_DIR, "review.db")
DATA_FILE = os.path.join(DB_DIR, "data.json")
SETTINGS_FILE = os.path.join(DB_DIR, "settings.json")

# 确保数据目录存在
os.makedirs(DB_DIR, exist_ok=True)

# Pydantic模型定义
class Node(BaseModel):
    id: str
    name: str
    done: bool = False
    lastreview: int = 0
    review_state: bool = False
    pos: List[float] = [0, 0]
    children: List['Node'] = []

class TimeRecord(BaseModel):
    id: Optional[int] = None
    node_id: str
    date: str
    start: int
    end: int

class TimerSession(BaseModel):
    node_id: str
    mode: str  # "learn" or "review"
    intervals: List[Dict[str, Any]]

class Settings(BaseModel):
    default_color: str = "#A0A0A0"
    toggle_done_color_project_tree: str = "#90EE90"
    start_review_color: str = "#ffd54f"
    toggle_done_color_stat: str = "#90caf9"
    tree_x_offset: int = 300
    tree_y_offset: int = 120
    timeline_num_segments: int = 9

# 数据库连接管理
@contextmanager
def get_db_connection(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

# 初始化数据库
def init_db():
    for db_path in [DB_LEARN, DB_REVIEW]:
        if not os.path.exists(db_path):
            with get_db_connection(db_path) as conn:
                c = conn.cursor()
                c.execute("""
                    CREATE TABLE record (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        node_id TEXT,
                        date TEXT,
                        start INTEGER,
                        end INTEGER
                    )
                """)
                conn.commit()

# 启动时初始化数据库
init_db()

# 工具函数
def load_project_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "name": "Root", 
        "id": "root", 
        "children": [], 
        "pos": [0, 0], 
        "done": False, 
        "lastreview": 0, 
        "review_state": False
    }

def save_project_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return Settings().dict()

def save_settings(settings_data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings_data, f, ensure_ascii=False, indent=2)

# API路由

@app.get("/")
async def root():
    return {"message": "Project Management API"}

# 项目树相关API
@app.get("/api/projects", response_model=Dict[str, Any])
async def get_projects():
    """获取项目树数据"""
    return load_project_data()

@app.post("/api/projects")
async def save_projects(data: Dict[str, Any]):
    """保存项目树数据"""
    save_project_data(data)
    return {"message": "Projects saved successfully"}

@app.post("/api/projects/node")
async def create_node(name: str, parent_id: str = "root"):
    """创建新节点"""
    data = load_project_data()
    new_node = {
        "id": str(uuid.uuid4()),
        "name": name,
        "done": False,
        "lastreview": 0,
        "review_state": False,
        "pos": [0, 0],
        "children": []
    }
    
    def add_to_parent(node, target_id):
        if node.get("id") == target_id:
            node.setdefault("children", []).append(new_node)
            return True
        for child in node.get("children", []):
            if add_to_parent(child, target_id):
                return True
        return False
    
    if add_to_parent(data, parent_id):
        save_project_data(data)
        return new_node
    else:
        raise HTTPException(status_code=404, detail="Parent node not found")

@app.delete("/api/projects/node/{node_id}")
async def delete_node(node_id: str):
    """删除节点"""
    data = load_project_data()
    
    def remove_node(node, target_id):
        children = node.get("children", [])
        for i, child in enumerate(children):
            if child.get("id") == target_id:
                children.pop(i)
                return True
            if remove_node(child, target_id):
                return True
        return False
    
    if remove_node(data, node_id):
        save_project_data(data)
        return {"message": "Node deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Node not found")

# 时间记录相关API
@app.get("/api/records/{mode}/{node_id}")
async def get_records(mode: str, node_id: str):
    """获取指定节点的时间记录"""
    db_path = DB_LEARN if mode == "learn" else DB_REVIEW
    with get_db_connection(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM record WHERE node_id = ?", (node_id,))
        records = c.fetchall()
        return [
            {
                "id": r[0],
                "node_id": r[1], 
                "date": r[2],
                "start": r[3],
                "end": r[4]
            } for r in records
        ]

@app.post("/api/records/{mode}")
async def add_record(mode: str, record: TimeRecord):
    """添加时间记录"""
    db_path = DB_LEARN if mode == "learn" else DB_REVIEW
    with get_db_connection(db_path) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO record (node_id, date, start, end) VALUES (?, ?, ?, ?)",
            (record.node_id, record.date, record.start, record.end)
        )
        conn.commit()
        return {"message": "Record added successfully"}

@app.post("/api/timer/complete")
async def complete_timer_session(session: TimerSession):
    """完成计时会话，保存记录"""
    db_path = DB_LEARN if session.mode == "learn" else DB_REVIEW
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    with get_db_connection(db_path) as conn:
        c = conn.cursor()
        for interval in session.intervals:
            if "end" in interval:
                c.execute(
                    "INSERT INTO record (node_id, date, start, end) VALUES (?, ?, ?, ?)",
                    (session.node_id, date, int(interval["start"]), int(interval["end"]))
                )
        conn.commit()
    
    # 如果是复习模式，更新lastreview时间
    if session.mode == "review":
        data = load_project_data()
        ts = int(time.time())
        
        def update_lastreview(node, target_id):
            if node.get("id") == target_id:
                node["lastreview"] = ts
                return True
            for child in node.get("children", []):
                if update_lastreview(child, target_id):
                    return True
            return False
        
        update_lastreview(data, session.node_id)
        save_project_data(data)
    
    return {"message": "Timer session completed successfully"}

# 统计相关API
@app.get("/api/stats/timeline")
async def get_timeline_data():
    """获取时间线数据"""
    data = load_project_data()
    node_id_name = {}
    
    def collect_names(node):
        node_id_name[node.get("id")] = node.get("name", "")
        for child in node.get("children", []):
            collect_names(child)
    
    collect_names(data)
    
    tasks = []
    for node_id, name in node_id_name.items():
        # 学习记录
        with get_db_connection(DB_LEARN) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM record WHERE node_id = ?", (node_id,))
            for record in c.fetchall():
                tasks.append({
                    "task": name,
                    "type": "Learn",
                    "start": record[3],
                    "end": record[4],
                    "date": record[2]
                })
        
        # 复习记录
        with get_db_connection(DB_REVIEW) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM record WHERE node_id = ?", (node_id,))
            for record in c.fetchall():
                tasks.append({
                    "task": name,
                    "type": "Review", 
                    "start": record[3],
                    "end": record[4],
                    "date": record[2]
                })
    
    return tasks

# 设置相关API
@app.get("/api/settings", response_model=Settings)
async def get_settings():
    """获取设置"""
    return load_settings()

@app.post("/api/settings")
async def save_settings_api(settings: Settings):
    """保存设置"""
    save_settings(settings.dict())
    return {"message": "Settings saved successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
