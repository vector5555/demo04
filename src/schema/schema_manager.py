import os
import json
from typing import Dict, List, Optional
from sqlalchemy import create_engine
from .schema_builder import SchemaBuilder

class SchemaManager:
    """
    管理不同角色的schema
    """
    def __init__(self, db_config_file: str):
        self.db_config_file = db_config_file
        self.db_config = None
        self.engine = None
        self.schema_builder = None
        
        # 加载数据库配置
        self._load_db_config()
    
    def _load_db_config(self):
        """加载数据库配置"""
        try:
            if os.path.exists(self.db_config_file):
                with open(self.db_config_file, 'r', encoding='utf-8') as f:
                    self.db_config = json.load(f)
                print(f"已加载数据库配置: {self.db_config_file}")
                
                # 创建数据库引擎
                conn_str = f"mysql+pymysql://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}"
                self.engine = create_engine(conn_str)
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