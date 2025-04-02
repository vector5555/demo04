import json
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, inspect, MetaData, Table, Column
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

class SchemaBuilder:
    """
    根据用户角色权限构建个性化数据库schema
    """
    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)
        self.metadata = MetaData()
        self.tables_info = {}
        self.relationships = {}
    
    def build_schema_for_role(self, role_permissions: List[Dict]) -> Dict:
        """
        根据角色权限构建schema
        
        Args:
            role_permissions: 角色权限列表，包含表名、字段列表和过滤条件
            
        Returns:
            构建好的schema字典
        """
        schema = {
            "tables": {},
            "relationships": []
        }
        
        # 处理每个表的权限
        for perm in role_permissions:
            db_name = perm.get("db_name")
            table_name = perm.get("table_name")
            field_list = perm.get("field_list", [])
            where_clause = perm.get("where_clause")
            field_info = perm.get("field_info", [])
            
            # 如果没有指定字段，则获取所有字段
            if not field_list:
                try:
                    columns = self.inspector.get_columns(table_name, schema=db_name)
                    field_list = [col["name"] for col in columns]
                except SQLAlchemyError as e:
                    print(f"获取表 {db_name}.{table_name} 的字段失败: {str(e)}")
                    continue
            
            # 获取表的详细信息
            table_info = self._get_table_info(db_name, table_name, field_list, field_info)
            if table_info:
                schema["tables"][f"{db_name}.{table_name}"] = table_info
                
                # 添加行级过滤条件
                if where_clause:
                    table_info["filter_condition"] = where_clause
        
        # 添加表关系信息
        schema["relationships"] = self._build_relationships(schema["tables"])
        
        return schema
    
    def _get_table_info(self, db_name: str, table_name: str, 
                        field_list: List[str], field_info: List[Dict]) -> Dict:
        """获取表的详细信息"""
        try:
            # 获取表的所有列
            columns = self.inspector.get_columns(table_name, schema=db_name)
            
            # 获取主键
            pk_columns = self.inspector.get_pk_constraint(table_name, schema=db_name)
            primary_keys = pk_columns.get("constrained_columns", [])
            
            # 获取外键
            foreign_keys = self.inspector.get_foreign_keys(table_name, schema=db_name)
            
            # 构建表信息
            table_info = {
                "name": table_name,
                "schema": db_name,
                "columns": [],
                "primary_keys": primary_keys,
                "foreign_keys": []
            }
            
            # 处理列信息
            for col in columns:
                if col["name"] in field_list:
                    # 查找字段的注释信息
                    comment = ""
                    for field in field_info:
                        if field.get("name") == col["name"]:
                            comment = field.get("comment", "")
                            break
                    
                    column_info = {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "comment": comment
                    }
                    
                    if col["name"] in primary_keys:
                        column_info["is_primary_key"] = True
                    
                    table_info["columns"].append(column_info)
            
            # 处理外键信息
            for fk in foreign_keys:
                fk_info = {
                    "column": fk["constrained_columns"],
                    "referred_schema": fk.get("referred_schema"),
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"]
                }
                table_info["foreign_keys"].append(fk_info)
                
                # 保存关系信息，用于后续构建关系图
                self._add_relationship(
                    db_name, table_name, fk["constrained_columns"],
                    fk.get("referred_schema", db_name), fk["referred_table"], fk["referred_columns"]
                )
            
            return table_info
        
        except SQLAlchemyError as e:
            print(f"获取表 {db_name}.{table_name} 的信息失败: {str(e)}")
            return None
    
    def _add_relationship(self, from_schema: str, from_table: str, from_cols: List[str],
                         to_schema: str, to_table: str, to_cols: List[str]):
        """添加表关系信息"""
        key = f"{from_schema}.{from_table}"
        if key not in self.relationships:
            self.relationships[key] = []
        
        self.relationships[key].append({
            "from_columns": from_cols,
            "to_schema": to_schema,
            "to_table": to_table,
            "to_columns": to_cols
        })
    
    def _build_relationships(self, tables: Dict) -> List[Dict]:
        """构建表关系列表"""
        relationships = []
        
        for table_key, rels in self.relationships.items():
            schema_name, table_name = table_key.split(".")
            
            # 只处理在权限范围内的表
            if table_key not in tables:
                continue
            
            for rel in rels:
                to_key = f"{rel['to_schema']}.{rel['to_table']}"
                
                # 只处理在权限范围内的关联表
                if to_key not in tables:
                    continue
                
                relationship = {
                    "from_table": table_name,
                    "from_schema": schema_name,
                    "from_columns": rel["from_columns"],
                    "to_table": rel["to_table"],
                    "to_schema": rel["to_schema"],
                    "to_columns": rel["to_columns"]
                }
                
                relationships.append(relationship)
        
        return relationships
    
    def save_schema(self, schema: Dict, file_path: str):
        """保存schema到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(schema, f, ensure_ascii=False, indent=2)
            print(f"Schema已保存到: {file_path}")
            return True
        except Exception as e:
            print(f"保存Schema失败: {str(e)}")
            return False