import os
import json
from typing import Dict, List, Optional
from sqlalchemy import create_engine, inspect
from .schema_builder import SchemaBuilder

class SchemaManager:
    """
    管理不同角色的schema
    """
    def __init__(self, db_url_or_config_file):
        """
        初始化SchemaManager
        
        Args:
            db_url_or_config_file: 可以是数据库URL字符串或配置文件路径
        """
        self.db_url = None
        self.db_config_file = None
        self.db_config = None
        self.engine = None
        self.schema_builder = None
        self._schema_info = None
        
        # 判断参数类型
        if isinstance(db_url_or_config_file, str):
            if db_url_or_config_file.endswith('.json'):
                # 是配置文件路径
                self.db_config_file = db_url_or_config_file
                self._load_db_config()
            else:
                # 是数据库URL
                self.db_url = db_url_or_config_file
                self.engine = create_engine(self.db_url)
                self.inspector = inspect(self.engine)
    
    def _load_db_config(self):
        """加载数据库配置"""
        try:
            if os.path.exists(self.db_config_file):
                with open(self.db_config_file, 'r', encoding='utf-8') as f:
                    self.db_config = json.load(f)
                print(f"已加载数据库配置: {self.db_config_file}")
                
                # 创建数据库引擎
                conn_str = f"mysql+pymysql://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config.get('database', '')}"
                self.db_url = conn_str
                self.engine = create_engine(conn_str)
                self.inspector = inspect(self.engine)
                self.schema_builder = SchemaBuilder(self.engine)
            else:
                print(f"数据库配置文件不存在: {self.db_config_file}")
        except Exception as e:
            print(f"加载数据库配置失败: {str(e)}")
    
    def build_schema_for_role(self, role_id: int, role_permissions: List[Dict]) -> Optional[Dict]:
        """为角色构建schema"""
        if not self.schema_builder:
            print("Schema构建器未初始化，请先加载数据库配置")
            return None
        
        try:
            # 构建schema
            schema = self.schema_builder.build_schema_for_role(role_permissions)
            return schema
        except Exception as e:
            print(f"为角色 {role_id} 构建schema失败: {str(e)}")
            return None
    
    def build_schemas_for_user(self, user_id: int, roles_permissions: Dict[int, List[Dict]]) -> Dict[int, Dict]:
        """为用户的所有角色构建schema"""
        schemas = {}
        
        for role_id, permissions in roles_permissions.items():
            schema = self.build_schema_for_role(role_id, permissions)
            if schema:
                schemas[role_id] = schema
        
        return schemas
        
    def get_user_schema(self, user_id, auth_db):
        """
        获取用户特定的schema信息
        
        Args:
            user_id: 用户ID或用户名
            auth_db: 认证数据库会话
        
        Returns:
            str: 用户可访问的schema信息
        """
        try:
            # 获取用户角色
            from ..database.models.role import UserRole, RolePermission, Role
            from ..database.models.user import User
            
            # 查询用户角色
            user_roles = auth_db.query(UserRole).filter(UserRole.user_id == user_id).all()
            if not user_roles:
                print(f"用户 {user_id} 没有分配角色")
                return "用户没有分配角色，无法获取schema信息"
                
            role_ids = [ur.role_id for ur in user_roles]
            
            # 获取角色权限
            permissions = auth_db.query(RolePermission).filter(RolePermission.role_id.in_(role_ids)).all()
            if not permissions:
                print(f"用户 {user_id} 的角色没有权限")
                return "用户角色没有权限，无法获取schema信息"
                
            # 构建用户可访问的schema
            schema_info = []
            
            # 确保inspector已初始化
            if not hasattr(self, 'inspector') or self.inspector is None:
                if self.engine:
                    self.inspector = inspect(self.engine)
                else:
                    print("数据库引擎未初始化")
                    return "数据库引擎未初始化，无法获取schema信息"
            
            # 收集允许的表和字段
            allowed_tables = set()
            allowed_fields = {}
            filter_conditions = {}
            
            for perm in permissions:
                if perm.table_name:
                    allowed_tables.add(perm.table_name)
                    
                    # 处理字段列表
                    if perm.field_list:
                        if perm.table_name not in allowed_fields:
                            allowed_fields[perm.table_name] = set()
                        
                        try:
                            # 处理field_list，确保它是字符串
                            if isinstance(perm.field_list, str):
                                fields = [f.strip() for f in perm.field_list.split(',')]
                            elif isinstance(perm.field_list, list):
                                fields = [f.strip() if isinstance(f, str) else str(f) for f in perm.field_list]
                            else:
                                # 如果是其他类型，转换为字符串
                                fields = [str(perm.field_list)]
                            
                            allowed_fields[perm.table_name].update(fields)
                        except Exception as e:
                            print(f"处理字段列表出错: {str(e)}")
                            # 出错时不限制字段
                    
                    # 添加过滤条件
                    if perm.where_clause:
                        try:
                            if perm.table_name not in filter_conditions:
                                filter_conditions[perm.table_name] = []
                            # 确保where_clause是字符串
                            where_clause = str(perm.where_clause) if perm.where_clause is not None else ""
                            if where_clause:
                                filter_conditions[perm.table_name].append(where_clause)
                        except Exception as e:
                            print(f"处理过滤条件出错: {str(e)}")
                            # 出错时不添加过滤条件
            
            # 如果没有允许的表，返回提示信息
            if not allowed_tables:
                return "用户没有权限访问任何表"

            print(f"允许的表: {allowed_tables}")
            
            # 从权限中提取数据库名称
            database_names = set()
            for perm in permissions:
                if hasattr(perm, 'db_name') and perm.db_name:
                    database_names.add(perm.db_name)
            
            print(f"从权限中提取的数据库名: {database_names}")
            
            # 检查inspector是否正确初始化
            if not hasattr(self, 'inspector') or self.inspector is None:
                print("警告: inspector未初始化，尝试重新初始化")
                if self.engine:
                    self.inspector = inspect(self.engine)
                else:
                    print("错误: 无法初始化inspector，engine为None")
                    return "数据库引擎未初始化，无法获取schema信息"
            
            # 尝试获取所有表名并打印
            try:
                print("开始获取所有表名...")
                if self.inspector:
                    print(f"inspector对象: {self.inspector}")
                    print(f"engine对象: {self.engine}")
                    
                    # 检查数据库URL是否包含数据库名
                    if self.db_url:
                        parts = self.db_url.split('/')
                        if len(parts) > 3 and not parts[-1]:  # 如果URL以/结尾但没有数据库名
                            print("警告: 数据库URL没有指定数据库名")
                            
                            # 使用从权限中提取的数据库名
                            if database_names:
                                db_name = next(iter(database_names))
                                print(f"使用权限中的数据库名: {db_name}")
                                new_url = f"{self.db_url}{db_name}"
                                # 安全地打印连接字符串
                                masked_url = new_url
                                if self.db_config and 'password' in self.db_config and self.db_config['password']:
                                    masked_url = new_url.replace(self.db_config['password'], '******')
                                print(f"尝试使用新的连接字符串: {masked_url}")
                                self.engine = create_engine(new_url)
                                self.inspector = inspect(self.engine)
                            # 如果没有从权限中提取到数据库名，尝试使用配置中的数据库名
                            elif self.db_config and 'database' in self.db_config and self.db_config['database']:
                                new_url = f"{self.db_url}{self.db_config['database']}"
                                print(f"尝试使用配置中的数据库名: {self.db_config['database']}")
                                self.engine = create_engine(new_url)
                                self.inspector = inspect(self.engine)
                    
                    print("调用get_table_names()方法...")
                    all_tables = self.inspector.get_table_names()
                    print(f"数据库中的所有表: {all_tables}")
                else:
                    print("inspector仍然为None，无法获取表名")
                    raise Exception("inspector未初始化")
            except Exception as e:
                print(f"获取表名列表失败: {str(e)}")
                return "数据库连接失败，无法获取schema信息"
                
            # 构建schema信息
            for table_name in allowed_tables:
                try:
                    print(f"正在处理表: {table_name}")
                    
                    # 检查表是否存在
                    try:
                        table_exists = table_name in self.inspector.get_table_names()
                        print(f"表 {table_name} 存在: {table_exists}")
                        if not table_exists:
                            print(f"表 {table_name} 不存在，跳过")
                            continue
                    except Exception as table_check_error:
                        print(f"检查表 {table_name} 是否存在时出错: {str(table_check_error)}")
                        continue

                    # 获取表结构
                    try:
                        columns = self.inspector.get_columns(table_name)
                        print(f"表 {table_name} 的列数: {len(columns)}")
                    except Exception as columns_error:
                        print(f"获取表 {table_name} 的列信息失败: {str(columns_error)}")
                        continue
                        
                    try:
                        primary_key = self.inspector.get_pk_constraint(table_name)
                        print(f"表 {table_name} 的主键: {primary_key}")
                    except Exception as pk_error:
                        print(f"获取表 {table_name} 的主键失败: {str(pk_error)}")
                        primary_key = {}
                        
                    try:
                        foreign_keys = self.inspector.get_foreign_keys(table_name)
                        print(f"表 {table_name} 的外键数: {len(foreign_keys)}")
                    except Exception as fk_error:
                        print(f"获取表 {table_name} 的外键失败: {str(fk_error)}")
                        foreign_keys = []
                    
                    # 构建表信息
                    table_info = f"Table '{table_name}':\n"
                    table_info += "Columns:\n"

                    print(table_info)
                    
                    for col in columns:
                        # 如果指定了允许的字段，且当前字段不在允许列表中，则跳过
                        if table_name in allowed_fields and col['name'] not in allowed_fields[table_name]:
                            continue
                            
                        # 获取列的注释信息
                        try:
                            # if col['comment']:
                            comment_text = col['comment']
                            if(comment_text==None):
                                comment_text=""
                            # comment_text = f" - {comment['text']}" if comment and comment.get('text') else ""
                        except Exception as comment_error:
                            print(f"获取列 {table_name}.{col['name']} 的注释失败: {str(comment_error)}")
                            comment_text = ""
                            
                        table_info += f"  - {col['name']}: {col['type']}{comment_text}"
                        # 添加安全检查，确保primary_key存在且包含constrained_columns
                        if primary_key and 'constrained_columns' in primary_key and primary_key['constrained_columns']:
                            if col['name'] in primary_key['constrained_columns']:
                                table_info += " (Primary Key)"
                        table_info += "\n"
                    
                    print(table_info)
                    
                    if foreign_keys:
                        table_info += "Foreign Keys:\n"
                        for fk in foreign_keys:
                            # 添加安全检查，确保外键信息完整
                            if 'referred_table' not in fk or 'constrained_columns' not in fk or 'referred_columns' not in fk:
                                continue
                                
                            # 只显示用户有权限的外键关系
                            if fk['referred_table'] not in allowed_tables:
                                continue
                            
                            # 确保constrained_columns和referred_columns不是None
                            if fk['constrained_columns'] is None or fk['referred_columns'] is None:
                                continue
                                
                            table_info += f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}\n"
                    
                    # 添加过滤条件信息
                    if table_name in filter_conditions and filter_conditions[table_name]:
                        table_info += "Filter Conditions:\n"
                        for condition in filter_conditions[table_name]:
                            if condition:  # 确保条件不为None或空
                                table_info += f"  - WHERE {condition}\n"
                    
                    schema_info.append(table_info)
                except Exception as e:
                    print(f"处理表 {table_name} 时出错: {str(e)}")
                    # 出错时跳过该表
            
            if not schema_info:
                return "无法获取任何表的schema信息"
                
            return "\n".join(schema_info)
            
        except Exception as e:
            print(f"获取用户schema失败: {str(e)}")
            return "无法获取数据库schema信息"
    
    def get_user_permissions(self, user_id: int, auth_db) -> Dict:
        """获取用户的权限信息"""
        try:
            from ..database.models.role import UserRole, RolePermission
            
            # 获取用户的角色
            user_roles = auth_db.query(UserRole).filter(UserRole.user_id == user_id).all()
            role_ids = [ur.role_id for ur in user_roles]
            
            if not role_ids:
                print(f"用户 {user_id} 没有分配角色")
                return {'allowed_tables': [], 'allowed_fields': {}, 'filter_conditions': {}}
            
            # 获取角色的权限
            permissions = auth_db.query(RolePermission).filter(
                RolePermission.role_id.in_(role_ids)
            ).all()
            
            # 打印权限记录，查看属性
            for perm in permissions:
                print(f"权限记录: {perm.__dict__}")
            
            # 处理权限信息
            allowed_tables = set()
            allowed_fields = {}
            filter_conditions = {}
            
            for perm in permissions:
                # 添加表权限 - 不要尝试访问permission_type
                allowed_tables.add(perm.table_name)
                
                # 处理字段权限
                if perm.field_list:
                    if perm.table_name not in allowed_fields:
                        allowed_fields[perm.table_name] = set()
                    
                    # 确保field_list是字符串
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
                    
                    if perm.where_clause is not None:
                        filter_conditions[perm.table_name].append(perm.where_clause)
            
            # 将集合转换为列表
            for table in allowed_fields:
                allowed_fields[table] = list(allowed_fields[table])
            
            result = {
                'allowed_tables': list(allowed_tables),
                'allowed_fields': allowed_fields,
                'filter_conditions': filter_conditions
            }
            
            print(f"用户 {user_id} 的权限信息: {result}")
            return result
            
        except Exception as e:
            print(f"获取用户权限失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'allowed_tables': [], 'allowed_fields': {}, 'filter_conditions': {}}