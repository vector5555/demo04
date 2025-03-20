@app.get("/schema")
async def get_schema():
    # 返回数据库 Schema 信息
    return {
        "tables": [
            {
                "name": "envom_origin",
                "columns": [
                    {"name": "CDMC", "type": "varchar"},
                    {"name": "CYRQ", "type": "datetime"},
                    {"name": "AQI", "type": "int"},
                    # ... 其他列信息
                ]
            }
            # ... 其他表信息
        ]
    }

@app.post("/query")
async def query(request: dict):
    # 从请求中获取 schema 信息，而不是重复查询数据库
    schema = request.get("schema")
    query_text = request.get("query_text")
    # ... 其他处理逻辑