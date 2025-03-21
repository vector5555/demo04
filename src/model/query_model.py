from typing import Dict, Any, Optional
import aiohttp
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import QueuePool
from ..context.query_context import QueryContext
import json
from pathlib import Path

class QueryModel:
    def __init__(self, db_url: str, api_key: str, api_url: str):
        self.engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        self.context_manager = QueryContext()
        self.api_key = api_key
        self.api_url = api_url
        print("正在初始化数据库连接...")
        # 在初始化时获取 schema 信息并缓存
        print("开始加载数据库 Schema 信息...")
        self._schema_info = self._get_schema_info()
        self._examples = self._load_examples()
        print(f"Schema 信息加载完成，长度: {len(self._schema_info)}")

    def _load_examples(self) -> str:
        try:
            feedback_path = Path(__file__).parent.parent.parent / 'feedback' / 'feedback_data.json'
            print(f"正在加载示例数据: {feedback_path}")
            with open(feedback_path, 'r', encoding='utf-8') as f:
                examples = json.load(f)
                example_text = []
                for example in examples:
                    example_text.append(f"User Query: {example['query']}\nSQL: {example['sql']}")
                return "\n\n".join(example_text)
        except Exception as e:
            print(f"加载示例数据失败: {str(e)}")
            return ""

    def _get_schema_info(self) -> str:
        print("正在获取数据库表结构...")
        inspector = inspect(self.engine)
        schema_info = []
        
        tables = inspector.get_table_names()
        print(f"发现 {len(tables)} 个数据表")
        
        for table_name in tables:
            print(f"正在处理表: {table_name}")
            columns = inspector.get_columns(table_name)
            primary_key = inspector.get_pk_constraint(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            table_info = f"Table '{table_name}':\n"
            table_info += "Columns:\n"
            for col in columns:
                table_info += f"  - {col['name']}: {col['type']}"
                if col['name'] in [pk for pk in primary_key['constrained_columns']]:
                    table_info += " (Primary Key)"
                table_info += "\n"
            
            if foreign_keys:
                table_info += "Foreign Keys:\n"
                for fk in foreign_keys:
                    table_info += f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}\n"
            
            schema_info.append(table_info)
            print(f"表 {table_name} 处理完成")
        
        return "\n".join(schema_info)

    @property
    def schema_info(self) -> str:
        # 使用属性装饰器，返回缓存的 schema 信息
        return self._schema_info

    async def generate_sql(self, query: str, context_id: str) -> str:
        try:
            print("\n=== 开始生成 SQL ===")
            print(f"接收到的查询: {query}")
            print(f"Context ID: {context_id}")
            print(f"API URL: {self.api_url}")
            
            context = self.context_manager.get_context(context_id)
            history = context['history'] if context else []
            
            if not self._schema_info:
                print("警告: Schema 信息为空")
                self._schema_info = self._get_schema_info()
            
            print("\n--- API 请求详情 ---")
            print(f"准备建立连接到: {self.api_url}")
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                print(f"请求头: {headers}")
                
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"""You are a SQL expert. Generate SQL query based on the schema and user query.

Examples:
{self._examples}

Return ONLY the SQL query without any explanation or markdown formatting."""
                        },
                        {
                            "role": "user",
                            "content": f"""Database Schema:\n{self._schema_info}\n\nUser Query: {query}"""
                        }
                    ],
                    "temperature": 0.0,
                    "max_tokens": 2000
                }
                print(f"请求体: {payload}")
                
                print("\n正在发送 POST 请求...")
                async with session.post(self.api_url, headers=headers, json=payload, timeout=30) as response:
                    print(f"请求已发送，等待响应...")
                    print(f"API 响应状态码: {response.status}")
                    
                    response_text = await response.text()
                    print(f"原始响应内容: {response_text}")
                    
                    if response.status != 200:
                        raise Exception(f"API 请求失败: {response_text}")
                    
                    result = await response.json()
                    print(f"解析后的响应内容: {result}")
                    
                    if not result.get("choices") or not result["choices"][0].get("message"):
                        raise Exception("API 响应格式错误")
                    
                    sql = result["choices"][0]["message"]["content"].strip()
                    print(f"\n生成的 SQL: {sql}")
                    
                    return sql
                                
        except aiohttp.ClientError as e:
            print(f"网络请求错误: {str(e)}")
            raise Exception(f"API 请求失败: {str(e)}")
        except Exception as e:
            print(f"\n=== SQL 生成错误 ===\n{str(e)}")
            raise Exception(f"SQL 生成失败: {str(e)}")

    async def execute_query(self, sql: str) -> Any:
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql))
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            print(f"Database error: {str(e)}")
            # 如果是连接错误，尝试重新连接
            if "MySQL server has gone away" in str(e):
                with self.engine.connect() as connection:
                    result = connection.execute(text(sql))
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in result.fetchall()]
            raise Exception(f"SQL执行错误: {str(e)}")