from fastapi import FastAPI, Request, Body
import json
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from .protocol.query_protocol import QueryRequest, QueryResponse
from .model.query_model import QueryModel

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置信息
DB_URL = "mysql+pymysql://root:sa123@localhost:3306/air"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-073ca480b9184dcf9e1be31f805a356b"

query_model = QueryModel(DB_URL, API_KEY, DEEPSEEK_API_URL)

@app.post("/query_nl")  # 改名为 query_nl，表示自然语言查询
async def process_query(request: QueryRequest) -> QueryResponse:
    # 创建或获取上下文
    context_id = request.context_id or query_model.context_manager.create_context()
    
    # 生成 SQL
    sql = await query_model.generate_sql(request.query_text, context_id)
    
    # 执行查询
    result = await query_model.execute_query(sql)
    
    # 更新上下文
    query_model.context_manager.update_context(context_id, {
        'query': request.query_text,
        'sql': sql,
        'result': result,
        'state': 'completed'
    })
    
    return QueryResponse(
        
        sql=sql,
        result=result,
        context_id=context_id,
        status='success'
    )

# 添加文件路径常量
FEEDBACK_FILE = "d:\\mycode\\demo04\\feedback\\feedback_data.json"

# 确保反馈目录存在
os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

@app.post("/execute_sql")  # 直接执行 SQL
async def execute_query(
    sql: str = Body(..., description="SQL语句")
):
    """直接执行SQL查询"""
    try:
        result = await query_model.execute_query(sql)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/execute_edited")  # 执行编辑后的 SQL
async def execute_edited_query(
    original_sql: str = Body(..., description="原始 SQL"),
    edited_sql: str = Body(..., description="编辑后的 SQL")
):
    """执行编辑后的 SQL 查询"""
    try:
        result = await query_model.execute_query(edited_sql)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/feedback")  # 反馈路由保持不变
async def feedback(request: Request):
    data = await request.json()
    query = data.get("query")
    sql = data.get("sql")
    rating = data.get("rating")
    
    feedback_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "sql": sql,
        "rating": rating
    }
    
    try:
        # 读取现有数据
        existing_data = []
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # 添加新数据
        existing_data.append(feedback_data)
        
        # 保存到文件
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
        print(f"反馈已保存 - 查询: {query}, SQL: {sql}, 评分: {rating}")
        return {"status": "success"}
        
    except Exception as e:
        print(f"保存反馈失败: {str(e)}")
        return {"status": "error", "message": "保存反馈失败"}