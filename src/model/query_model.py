from typing import Dict, Any, Optional, Tuple, List
import aiohttp
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import QueuePool
from ..context.query_context import QueryContext
import json
from pathlib import Path
from ..vector_store.feedback_store import FeedbackVectorStore
from ..schema.schema_manager import SchemaManager  # 导入SchemaManager
from ..database.models.role import RolePermission  # 导入角色权限模型
from fastapi import Request  # 添加这一行导入Request
from ..validator.sql_validator import SQLValidator  # 导入SQL校验器

class QueryModel:
    def __init__(self, db_url: str, api_key: str, api_url: str, model_name: str = "deepseek-chat", 
                 temperature: float = 0.7, max_tokens: int = 2000, top_p: float = 0.95):
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
        # 保存模型参数
        self.model_params = {
            "model": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        # 初始化SchemaManager
        db_config_path = Path(__file__).parent.parent.parent / 'config' / 'db_config.json'
        self.schema_manager = SchemaManager(str(db_config_path))
        
        # 初始化SQL校验器
        self.sql_validator = SQLValidator()
        
        print("正在初始化数据库连接...")
        # 不在初始化时加载schema信息，而是设置为空字符串
        print("跳过加载数据库Schema信息，将在用户登录后按需加载...")
        self._schema_info = ""
        self._examples = self._load_examples()
        self.vector_store = FeedbackVectorStore()
        print("向量数据库加载完成")

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

    def _get_schema_info(self, user_id=None, auth_db=None) -> str:
        print("正在获取数据库表结构...")
        inspector = inspect(self.engine)
        schema_info = []
        
        # 如果提供了用户ID和auth_db，则获取用户的权限信息
        allowed_tables = None
        allowed_fields = {}
        filter_conditions = {}
        
        if user_id and auth_db:
            try:
                from ..database.models.role import UserRole, RolePermission
                # 获取用户的角色
                user_roles = auth_db.query(UserRole).filter(UserRole.user_id == user_id).all()
                role_ids = [ur.role_id for ur in user_roles]
                
                if role_ids:
                    # 获取角色的权限
                    permissions = auth_db.query(RolePermission).filter(
                        RolePermission.role_id.in_(role_ids)
                    ).all()
                    
                    # 处理权限信息
                    allowed_tables = set()
                    for perm in permissions:
                        allowed_tables.add(perm.table_name)
                        
                        # 处理字段权限
                        if perm.field_list:
                            if perm.table_name not in allowed_fields:
                                allowed_fields[perm.table_name] = set()
                            # 修复这里：确保field_list是字符串
                            if isinstance(perm.field_list, str):
                                fields = [field.strip() for field in perm.field_list.split(',') if field.strip()]
                            elif isinstance(perm.field_list, list):
                                fields = [str(field).strip() for field in perm.field_list]
                            else:
                                fields = [str(perm.field_list)]
                            allowed_fields[perm.table_name].update(fields)
                        
                        # 处理过滤条件
                        if perm.where_clause:
                            if perm.table_name not in filter_conditions:
                                filter_conditions[perm.table_name] = []
                            # 确保where_clause不是None
                            if perm.where_clause is not None:
                                filter_conditions[perm.table_name].append(perm.where_clause)
                
                print(f"用户 {user_id} 有权限访问的表: {allowed_tables}")
            except Exception as e:
                print(f"获取用户权限失败: {str(e)}")
                # 出错时不限制表访问
                allowed_tables = None
        
        tables = inspector.get_table_names()
        print(f"发现 {len(tables)} 个数据表")
        
        for table_name in tables:
            # 如果指定了允许的表，且当前表不在允许列表中，则跳过
            if allowed_tables is not None and table_name not in allowed_tables:
                print(f"表 {table_name} 不在用户权限范围内，跳过")
                continue
                
            print(f"正在处理表: {table_name}")
            try:
                columns = inspector.get_columns(table_name)
                primary_key = inspector.get_pk_constraint(table_name)
                foreign_keys = inspector.get_foreign_keys(table_name)
                
                table_info = f"Table '{table_name}':\n"
                table_info += "Columns:\n"
                
                for col in columns:
                    # 如果指定了允许的字段，且当前字段不在允许列表中，则跳过
                    if table_name in allowed_fields and col['name'] not in allowed_fields[table_name]:
                        continue
                        
                    table_info += f"  - {col['name']}: {col['type']}"
                    # 添加安全检查，确保primary_key存在且包含constrained_columns
                    if primary_key and 'constrained_columns' in primary_key and primary_key['constrained_columns']:
                        if col['name'] in primary_key['constrained_columns']:
                            table_info += " (Primary Key)"
                    table_info += "\n"
                
                if foreign_keys:
                    table_info += "Foreign Keys:\n"
                    for fk in foreign_keys:
                        # 添加安全检查，确保外键信息完整
                        if 'referred_table' in fk and 'constrained_columns' in fk and 'referred_columns' in fk:
                            # 只显示用户有权限的外键关系
                            if allowed_tables is not None and fk['referred_table'] not in allowed_tables:
                                continue
                            table_info += f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}\n"
                
                # 添加过滤条件信息
                if table_name in filter_conditions and filter_conditions[table_name]:
                    table_info += "Filter Conditions:\n"
                    for condition in filter_conditions[table_name]:
                        if condition:  # 确保条件不为None或空
                            table_info += f"  - WHERE {condition}\n"
                
                schema_info.append(table_info)
                print(f"表 {table_name} 处理完成")
            except Exception as e:
                print(f"处理表 {table_name} 时出错: {str(e)}")
                # 出错时跳过该表，继续处理其他表
                continue
        
        if not schema_info:
            return "无法获取任何表的schema信息"
            
        return "\n".join(schema_info)

    @property
    def schema_info(self) -> str:
        # 使用属性装饰器，返回缓存的 schema 信息
        return self._schema_info

    async def generate_sql(self, request: Request, query: str, context_id: str, user_id: Optional[int] = None, auth_db = None) -> str:
        try:
            print("\n=== 开始生成 SQL ===")
            print(f"接收到的查询: {query}")
            
            # 获取相似的示例
            similar_examples = self.vector_store.find_similar_examples(query)
            print(f"找到 {len(similar_examples)} 个相似示例")
            
            examples_text = []
            for example in similar_examples:
                examples_text.append(f"User Query: {example['query']}\nSQL: {example['sql']}")
            examples_prompt = "\n\n".join(examples_text)
            
            context = self.context_manager.get_context(context_id)
            history = context['history'] if context else []
            
            # 获取用户的个性化schema
            schema_info = ""
            # 删除这两行错误代码
            # user_id = Depends(get_current_user_id)
            # auth_db = Depends(get_auth_db)
            
            # 使用传入的user_id和auth_db参数
            if user_id and auth_db:
                # 如果提供了用户ID和auth_db，获取用户特定的schema
                schema_info = self.schema_manager.get_user_schema(user_id, auth_db)
                print(f"Schema_info:{schema_info}")
                print(f"获取用户 {user_id} 的个性化schema")
            else:
                # 如果没有提供用户信息，获取完整的schema（仅用于开发/测试）
                if not self._schema_info:
                    print("警告: Schema 信息为空，获取完整schema")
                    self._schema_info = self._get_schema_info()
                schema_info = self._schema_info
                print("使用完整schema（仅用于开发/测试）")
            
            if not schema_info:
                raise Exception("无法获取数据库schema信息")
            
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
                    "model": self.model_params["model"],  # 使用模型参数
                    "messages": [
                        {
                            "role": "system",
                            "content": f"""你是一个SQL专家。请根据提供的数据库结构和用户查询，生成符合以下权限约束的SQL查询语句。

权限约束：
1. 你只能查询用户有权限访问的表和字段
2. 必须应用指定的过滤条件（如果有）
3. 不要尝试绕过这些限制
4. 如果用户请求访问未授权的表或字段，返回以"ERROR:"开头的消息，说明权限问题

相似查询示例：
{examples_prompt}

返回格式要求：
- 对于有效查询：仅返回SQL查询语句，不要包含任何解释或markdown格式
- 对于无权限查询：返回以"ERROR:"开头的简短消息，例如"ERROR: 您没有权限访问请求的表或字段"
"""
                        },
                        {
                            "role": "user",
                            "content": f"""数据库结构：
{schema_info}

用户查询: {query}"""
                        }
                    ],
                    "temperature": self.model_params["temperature"],  # 使用模型参数
                    "max_tokens": self.model_params["max_tokens"]     # 使用模型参数
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

    async def validate_sql(self, sql: str, user_id: int = None, auth_db = None) -> Tuple[bool, str, Optional[str]]:
        """验证SQL是否符合用户权限"""
        try:
            print(f"验证SQL，用户ID: {user_id}, auth_db是否存在: {auth_db is not None}")
            
            # 获取用户权限信息
            allowed_tables = []
            allowed_fields = {}
            filter_conditions = {}
            
            if user_id and auth_db:
                # 从schema_manager获取用户权限信息
                user_permissions = self.schema_manager.get_user_permissions(user_id, auth_db)
                allowed_tables = user_permissions.get('allowed_tables', [])
                allowed_fields = user_permissions.get('allowed_fields', {})
                filter_conditions = user_permissions.get('filter_conditions', {})
            else:
                # 测试/开发模式，允许所有表和字段
                print("警告: 未提供用户ID，使用完全权限进行验证")
                # 获取所有表和字段
                inspector = inspect(self.engine)
                allowed_tables = inspector.get_table_names()
                for table in allowed_tables:
                    columns = inspector.get_columns(table)
                    allowed_fields[table] = [col['name'] for col in columns]
            
            # 调用SQL校验器验证SQL
            return self.sql_validator.validate_sql(sql, allowed_tables, allowed_fields, filter_conditions)
            
        except Exception as e:
            print(f"SQL验证错误: {str(e)}")
            return False, f"SQL验证失败: {str(e)}", None

    async def execute_query(self, sql: str, user_id: int = None, auth_db = None) -> Any:
        """执行SQL查询，添加权限验证"""
        try:
            # 验证SQL
            is_valid, error_msg, corrected_sql = await self.validate_sql(sql, user_id, auth_db)
            
            if not is_valid:
                raise Exception(f"SQL权限验证失败: {error_msg}")
            
            # 如果有修正后的SQL，使用修正后的版本
            if corrected_sql:
                print(f"使用修正后的SQL: {corrected_sql}")
                sql = corrected_sql
            print(f"SQL开始执行")
            
            # 执行查询
            try:
                with self.engine.connect() as connection:
                    # 开始事务
                    with connection.begin():
                        print(f"执行SQL: {sql}")
                        result = connection.execute(text(sql))
                        columns = result.keys()
                        rows = result.fetchall()
                        print(f"查询成功，获取到 {len(rows)} 条记录")
                        result_list = [dict(zip(columns, row)) for row in rows]
                print(f"SQL执行成功")
                return result_list
            except Exception as e:
                print(f"SQL执行错误: {str(e)}")
                # 如果是连接错误，尝试重新连接
                if "MySQL server has gone away" in str(e):
                    try:
                        print("尝试重新连接数据库...")
                        with self.engine.connect() as connection:
                            with connection.begin():
                                result = connection.execute(text(sql))
                                columns = result.keys()
                                rows = result.fetchall()
                                print(f"重连成功，获取到 {len(rows)} 条记录")
                                return [dict(zip(columns, row)) for row in rows]
                    except Exception as retry_error:
                        print(f"重连失败: {str(retry_error)}")
                        raise Exception(f"SQL执行错误(重连失败): {str(retry_error)}")
                raise Exception(f"SQL执行错误: {str(e)}")
        except Exception as e:
            print(f"执行查询失败: {str(e)}")
            raise Exception(f"执行查询失败: {str(e)}")

    async def execute_edited_query(self, original_sql: str, edited_sql: str) -> Any:
        """执行编辑后的 SQL 查询"""
        try:
            print(f"\n=== 执行编辑后的 SQL ===")
            print(f"编辑后的 SQL: {edited_sql}")
            
            # 直接执行编辑后的 SQL
            result = await self.execute_query(edited_sql)
            return result
            
        except Exception as e:
            print(f"执行编辑后的 SQL 失败: {str(e)}")
            raise Exception(f"执行失败: {str(e)}")

    # 添加获取用户个性化schema的方法
    def get_user_schema(self, user_id: int, auth_db) -> str:
        """
        获取用户的个性化schema
        
        Args:
            user_id: 用户ID
            auth_db: 认证数据库会话
            
        Returns:
            用户的个性化schema字符串
        """
        try:
            # 获取用户的角色
            from ..database.models.role import UserRole
            user_roles = auth_db.query(UserRole).filter(UserRole.user_id == user_id).all()
            role_ids = [ur.role_id for ur in user_roles]
            
            if not role_ids:
                print(f"用户 {user_id} 没有分配角色，使用默认schema")
                return self._schema_info
            
            # 获取角色的权限
            roles_permissions = {}
            for role_id in role_ids:
                permissions = auth_db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
                roles_permissions[role_id] = [
                    {
                        "db_name": perm.db_name,
                        "table_name": perm.table_name,
                        "field_list": perm.field_list.split(',') if isinstance(perm.field_list, str) and perm.field_list else [],
                        "where_clause": perm.where_clause
                    } for perm in permissions
                ]
            
            # 构建用户的schema
            schemas = self.schema_manager.build_schemas_for_user(user_id, roles_permissions)
            
            # 将schema转换为字符串格式
            schema_str = []
            for role_id, schema in schemas.items():
                for table_key, table_info in schema["tables"].items():
                    table_str = f"Table '{table_info['name']}':\n"
                    table_str += "Columns:\n"
                    
                    for col in table_info["columns"]:
                        col_str = f"  - {col['name']}: {col['type']}"
                        if col.get("is_primary_key"):
                            col_str += " (Primary Key)"
                        if col.get("comment"):
                            col_str += f" // {col['comment']}"
                        table_str += col_str + "\n"
                    
                    if table_info.get("foreign_keys"):
                        table_str += "Foreign Keys:\n"
                        for fk in table_info["foreign_keys"]:
                            table_str += f"  - {fk['column']} -> {fk['referred_table']}.{fk['referred_columns']}\n"
                    
                    if table_info.get("filter_condition"):
                        table_str += f"Filter Condition: {table_info['filter_condition']}\n"
                    
                    schema_str.append(table_str)
            
            return "\n".join(schema_str)
            
        except Exception as e:
            print(f"获取用户schema失败: {str(e)}")
            # 出错时返回默认schema
            return self._schema_info