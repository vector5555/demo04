"""
SQL解析器模块 - 用于解析SQL语句
"""
from typing import Dict, List, Set, Tuple, Optional
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Comparison
import re

class SQLParser:
    """
    SQL解析器类，提供更高级的SQL解析功能
    """
    
    @staticmethod
    def parse_sql(sql: str) -> Dict:
        """
        解析SQL语句，返回结构化信息
        
        Args:
            sql: SQL查询语句
            
        Returns:
            Dict: 包含SQL结构信息的字典
        """
        result = {
            'type': '',
            'tables': [],
            'fields': {},
            'where_conditions': [],
            'joins': [],
            'aliases': {}
        }
        
        try:
            # 解析SQL
            parsed = sqlparse.parse(sql)
            if not parsed:
                return result
                
            stmt = parsed[0]
            
            # 获取SQL类型
            result['type'] = stmt.get_type().lower()
            
            # 提取表名和别名
            SQLParser._extract_tables_and_aliases(stmt, result)
            
            # 提取字段
            SQLParser._extract_fields(stmt, result)
            
            # 提取WHERE条件
            SQLParser._extract_where_conditions(stmt, result)
            
            # 提取JOIN
            SQLParser._extract_joins(stmt, result)
            
            return result
            
        except Exception as e:
            print(f"SQL解析错误: {str(e)}")
            return result
    
    @staticmethod
    def _extract_tables_and_aliases(stmt, result: Dict):
        """提取表名和别名"""
        # 使用正则表达式提取，因为sqlparse的API不总是可靠
        sql_str = str(stmt)
        
        # 提取FROM子句
        from_clause = re.search(r'FROM\s+(.*?)(?:WHERE|GROUP BY|ORDER BY|LIMIT|$)', 
                               sql_str, re.IGNORECASE | re.DOTALL)
        
        if not from_clause:
            return
            
        from_text = from_clause.group(1)
        
        # 提取表名和别名
        # 匹配 "table AS alias", "table alias" 或 "table"
        table_pattern = r'([a-zA-Z0-9_\.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
        
        tables = []
        aliases = {}
        
        for match in re.finditer(table_pattern, from_text, re.IGNORECASE):
            table = match.group(1)
            alias = match.group(2)
            
            if table.lower() not in ('join', 'inner', 'left', 'right', 'full', 'outer', 'cross'):
                tables.append(table)
                
                if alias:
                    aliases[alias] = table
        
        result['tables'] = tables
        result['aliases'] = aliases
    
    @staticmethod
    def _extract_fields(stmt, result: Dict):
        """提取字段"""
        sql_str = str(stmt)
        
        # 提取SELECT子句
        select_clause = re.search(r'SELECT\s+(.*?)\s+FROM', sql_str, re.IGNORECASE | re.DOTALL)
        
        if not select_clause:
            return
            
        select_text = select_clause.group(1)
        
        # 分割字段
        fields = [f.strip() for f in select_text.split(',')]
        fields_dict = {}
        
        for field in fields:
            # 处理 table.field 或 alias.field 格式
            if '.' in field:
                parts = field.split('.')
                table_or_alias = parts[0].strip()
                column = parts[1].strip()
                
                # 如果是别名，转换为实际表名
                table = result['aliases'].get(table_or_alias, table_or_alias)
                
                if table not in fields_dict:
                    fields_dict[table] = []
                fields_dict[table].append(column)
            else:
                # 如果没有指定表名，假设字段属于FROM子句中的第一个表
                if result['tables']:
                    table = result['tables'][0]
                    if table not in fields_dict:
                        fields_dict[table] = []
                    fields_dict[table].append(field)
        
        result['fields'] = fields_dict
    
    @staticmethod
    def _extract_where_conditions(stmt, result: Dict):
        """提取WHERE条件"""
        sql_str = str(stmt)
        
        # 提取WHERE子句
        where_clause = re.search(r'WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|$)', 
                                sql_str, re.IGNORECASE | re.DOTALL)
        
        if not where_clause:
            return
            
        where_text = where_clause.group(1)
        
        # 分割条件（这是一个简化处理，实际上需要考虑括号和逻辑运算符）
        conditions = []
        
        # 先按AND分割
        and_parts = where_text.split(' AND ')
        
        for part in and_parts:
            # 再按OR分割
            or_parts = part.split(' OR ')
            conditions.extend(or_parts)
        
        result['where_conditions'] = [cond.strip() for cond in conditions]
    
    @staticmethod
    def _extract_joins(stmt, result: Dict):
        """提取JOIN信息"""
        sql_str = str(stmt)
        
        # 匹配各种JOIN
        join_pattern = r'((?:INNER|LEFT|RIGHT|FULL|OUTER|CROSS)?\s*JOIN)\s+([a-zA-Z0-9_\.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?\s+ON\s+(.*?)(?:(?:INNER|LEFT|RIGHT|FULL|OUTER|CROSS)?\s*JOIN|WHERE|GROUP BY|ORDER BY|LIMIT|$)'
        
        joins = []
        
        for match in re.finditer(join_pattern, sql_str, re.IGNORECASE | re.DOTALL):
            join_type = match.group(1).strip()
            table = match.group(2)
            alias = match.group(3)
            condition = match.group(4).strip()
            
            join_info = {
                'type': join_type,
                'table': table,
                'alias': alias,
                'condition': condition
            }
            
            joins.append(join_info)
            
            # 添加到表和别名列表
            if table not in result['tables']:
                result['tables'].append(table)
                
            if alias:
                result['aliases'][alias] = table
        
        result['joins'] = joins