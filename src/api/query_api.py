from fastapi import APIRouter, Body, Depends
from ..model.query_model import QueryModel
from ..dependencies import get_query_model

# 创建路由实例
router = APIRouter()

@router.post("/execute_edited")
async def execute_edited_query(
    original_sql: str = Body(..., description="原始 SQL"),
    edited_sql: str = Body(..., description="编辑后的 SQL"),
    query_model: QueryModel = Depends(get_query_model)
):
    """执行编辑后的 SQL 查询"""
    try:
        print(f"接收到编辑后的SQL请求：\n原始SQL: {original_sql}\n编辑后SQL: {edited_sql}")
        
        # 验证并执行编辑后的查询
        if not edited_sql.strip():
            raise Exception("编辑后的SQL不能为空")
            
        result = await query_model.execute_edited_query(original_sql, edited_sql)
        print("SQL执行完成，返回结果")
        return {"status": "success", "data": result}
    except Exception as e:
        print(f"执行失败: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.post("/query")
async def execute_query(
    sql: str = Body(..., description="SQL语句"),
    query_model: QueryModel = Depends(get_query_model)
):
    """直接执行SQL查询"""
    try:
        print(f"接收到SQL查询请求：{sql}")
        
        if not sql.strip():
            raise Exception("SQL语句不能为空")
            
        result = await query_model.execute_query(sql)
        print("SQL执行完成，返回结果")
        return {"status": "success", "data": result}
    except Exception as e:
        print(f"执行失败: {str(e)}")
        return {"status": "error", "message": str(e)}