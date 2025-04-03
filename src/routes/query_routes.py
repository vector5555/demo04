from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os

from ..protocol.query_protocol import QueryRequest, QueryResponse
from ..utils.auth import verify_token, get_current_user_id  # 添加get_current_user_id导入
from ..model.query_model import QueryModel
from ..config.auth_db import get_auth_db  # 添加get_auth_db导入

router = APIRouter(tags=["查询"])

# 反馈文件路径
FEEDBACK_FILE = "feedback\\feedback_data.json"
os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

# 依赖项：获取查询模型
def get_query_model():
    from ..main import query_model
    return query_model

@router.post("/query_nl", dependencies=[Depends(verify_token)])
async def process_query(request: QueryRequest, query_model: QueryModel = Depends(get_query_model)) -> QueryResponse:
    try:
        print(f"收到查询请求: {request.query_text}")
        
        context_id = request.context_id or query_model.context_manager.create_context()
        print(f"上下文ID: {context_id}")
        
        # 修改这里，添加request参数
        sql = await query_model.generate_sql(Request(scope={"type": "http"}), request.query_text, context_id)
        print(f"生成的SQL: {sql}")
        
        print("开始执行SQL查询...")
        result = await query_model.execute_query(sql)
        print(f"查询结果: {result}")
        
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
    except Exception as e:
        print(f"查询处理出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute_sql", dependencies=[Depends(verify_token)])
async def execute_query(
    sql: str = Body(..., description="SQL语句"),
    query_model: QueryModel = Depends(get_query_model)
):
    """直接执行SQL查询"""
    try:
        result = await query_model.execute_query(sql)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/execute_edited", dependencies=[Depends(verify_token)])
async def execute_edited_query(
    original_sql: str = Body(..., description="原始 SQL"),
    edited_sql: str = Body(..., description="编辑后的 SQL"),
    query_model: QueryModel = Depends(get_query_model)
):
    """执行编辑后的 SQL 查询"""
    try:
        result = await query_model.execute_query(edited_sql)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/feedback", dependencies=[Depends(verify_token)])
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


# 修改路由路径，避免与上面的路由冲突
@router.post("/query_nl_with_auth", dependencies=[Depends(verify_token)])
async def query_natural_language(
    request: Request,
    query_data: dict = Body(...),
    query_model: QueryModel = Depends(get_query_model),
    user_id: int = Depends(get_current_user_id),
    auth_db: Session = Depends(get_auth_db)
):
    """处理自然语言查询（带权限控制）"""
    query_text = query_data.get("query_text")
    context_id = query_data.get("context_id")
    
    try:
        # 传递request参数
        sql = await query_model.generate_sql(request, query_text, context_id, user_id, auth_db)
        result = await query_model.execute_query(sql)
        
        # 执行SQL查询
        result = await query_model.execute_query(sql)
        
        # 更新上下文
        if not context_id:
            context_id = query_model.context_manager.create_context()
        
        query_model.context_manager.update_context(context_id, {
            'query': query_text,
            'sql': sql,
            'result': result,
            'state': 'completed'
        })
        
        return {
            "sql": sql,
            "result": result,
            "context_id": context_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))