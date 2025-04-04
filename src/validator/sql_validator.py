"""
SQL校验模块 - 用于验证生成的SQL是否符合用户权限
"""
from typing import Dict, List, Tuple, Optional, Any
import sqlparse
import re
from sqlalchemy import text

class SQLValidator:
    """
    SQL校验器类，用于验证SQL查询是否符合用户权限
    """
    
    def __init__(self):
        """初始化SQL校验器"""
        pass
        
    def validate_sql(self, sql: str, allowed_tables: List[str], 
                     allowed_fields: Dict[str, List[str]], 
                     filter_conditions: Dict[str, List[str]]) -> Tuple[bool, str, Optional[str]]:
        """
        验证SQL是否符合用户权限
        
        Args:
            sql: 要验证的SQL查询语句
            allowed_tables: 用户有权限访问的表列表
            allowed_fields: 用户有权限访问的字段字典，格式为 {表名: [字段名列表]}
            filter_conditions: 必须应用的过滤条件，格式为 {表名: [过滤条件列表]}
            
        Returns:
            Tuple[bool, str, Optional[str]]: 
                - 验证是否通过
                - 错误信息（如果验证失败）
                - 修正后的SQL（如果可以自动修正）
        """
        try:
            print(f"\n=== 开始验证SQL ===")
            print(f"原始SQL: {sql}")
            
            # 解析SQL
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "无法解析SQL语句", None
                
            # 获取SQL类型
            stmt = parsed[0]
            stmt_type = stmt.get_type().lower()
            
            # 只允许SELECT语句
            if stmt_type != 'select':
                return False, f"不支持的SQL类型: {stmt_type}，仅允许SELECT查询", None
            
            # 提取表名
            tables = self._extract_tables(sql)
            print(f"提取的表: {tables}")
            
            # 检查表权限
            for table in tables:
                if table not in allowed_tables:
                    return False, f"无权访问表: {table}", None
            
            # 提取字段
            fields = self._extract_fields(sql)
            print(f"提取的字段: {fields}")
            
            # 检查字段权限
            for table, cols in fields.items():
                if table in allowed_fields:
                    for col in cols:
                        # 跳过*号，因为我们已经验证了表权限
                        if col == '*':
                            continue
                        # 跳过空字段名或纯数字（可能是常量）
                        if not col or col.isdigit():
                            continue
                        # 跳过括号（可能是未正确解析的表达式）
                        if '(' in col or ')' in col:
                            print(f"警告: 跳过可能是表达式的字段: {col}")
                            continue
                        # 检查字段权限
                        if col not in allowed_fields[table]:
                            print(f"字段权限检查失败: 表 {table} 的字段 {col} 不在允许列表中 {allowed_fields[table]}")
                            return False, f"无权访问字段: {table}.{col}", None
            
            # 检查过滤条件
            missing_conditions = []
            for table in tables:
                if table in filter_conditions and filter_conditions[table]:
                    # 检查每个必要的过滤条件是否已应用
                    for condition in filter_conditions[table]:
                        if condition and not self._check_condition_applied(sql, table, condition):
                            missing_conditions.append((table, condition))
            
            # 如果有缺失的过滤条件，尝试修正SQL
            if missing_conditions:
                corrected_sql = self._apply_missing_conditions(sql, missing_conditions)
                if corrected_sql:
                    print(f"已修正SQL: {corrected_sql}")
                    return True, "已自动应用必要的过滤条件", corrected_sql
                else:
                    conditions_str = "; ".join([f"{table}: {cond}" for table, cond in missing_conditions])
                    return False, f"缺少必要的过滤条件: {conditions_str}", None
            
            print("SQL验证通过")
            return True, "", None
            
        except Exception as e:
            print(f"SQL验证错误: {str(e)}")
            return False, f"SQL验证失败: {str(e)}", None
    
    def _extract_tables(self, sql: str) -> List[str]:
        """
        从SQL中提取表名
        
        这是一个简化版实现，实际应用中可能需要更复杂的解析
        """
        # 使用正则表达式提取FROM和JOIN子句中的表名
        from_pattern = r'FROM\s+([a-zA-Z0-9_]+)'
        join_pattern = r'JOIN\s+([a-zA-Z0-9_]+)'
        
        from_tables = re.findall(from_pattern, sql, re.IGNORECASE)
        join_tables = re.findall(join_pattern, sql, re.IGNORECASE)
        
        return list(set(from_tables + join_tables))
    
    def _extract_fields(self, sql: str) -> Dict[str, List[str]]:
        """
        从SQL中提取字段名及其所属表
        
        处理复杂的字段表达式，包括聚合函数和CAST等
        """
        # 提取SELECT子句
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not select_match:
            return {}
            
        select_clause = select_match.group(1)
        fields_dict = {}
        
        # 处理表别名
        tables = self._extract_tables(sql)
        aliases = self._extract_aliases(sql)
        
        # 使用更复杂的方法拆分字段，考虑括号嵌套
        fields = self._split_select_fields(select_clause)
        
        for field in fields:
            # 尝试提取原始字段名，忽略函数和别名
            original_field = self._extract_original_field(field)
            
            # 如果能够提取出表名和字段名
            if '.' in original_field:
                parts = original_field.split('.')
                table = parts[0].strip()
                column = parts[1].strip()
                
                # 处理别名
                if table in aliases:
                    table = aliases[table]
                
                if table not in fields_dict:
                    fields_dict[table] = []
                fields_dict[table].append(column)
            else:
                # 如果没有指定表名，假设字段属于FROM子句中的第一个表
                if tables:
                    table = tables[0]
                    if table not in fields_dict:
                        fields_dict[table] = []
                    fields_dict[table].append(original_field)
        
        return fields_dict
    
    def _split_select_fields(self, select_clause: str) -> List[str]:
        """
        智能拆分SELECT子句中的字段，处理括号嵌套和逗号
        """
        fields = []
        current_field = ""
        bracket_count = 0
        
        for char in select_clause:
            if char == ',' and bracket_count == 0:
                # 只有在不在括号内时，逗号才表示字段分隔
                if current_field.strip():
                    fields.append(current_field.strip())
                current_field = ""
            else:
                current_field += char
                if char == '(':
                    bracket_count += 1
                elif char == ')':
                    bracket_count -= 1
        
        # 添加最后一个字段
        if current_field.strip():
            fields.append(current_field.strip())
        
        return fields
    
    def _extract_original_field(self, field_expr: str) -> str:
        """
        从字段表达式中提取原始字段名
        例如：从 "AVG(CAST(table.column AS DECIMAL)) AS avg_col" 提取 "table.column"
        """
        # 处理AS别名
        if ' AS ' in field_expr.upper():
            field_expr = field_expr.split(' AS ')[0].strip()
        
        # 打印原始表达式，帮助调试
        print(f"处理字段表达式: {field_expr}")
        
        # 处理聚合函数和CAST表达式
        field_name = field_expr
        
        # 特殊处理CAST表达式中的字段
        cast_pattern = r'CAST\s*\(\s*([^()]+?)\s+AS\s+'
        cast_match = re.search(cast_pattern, field_name, re.IGNORECASE)
        if cast_match:
            field_name = cast_match.group(1).strip()
            print(f"从CAST提取字段: {field_name}")
            return field_name
        
        # 处理嵌套函数，如AVG(CAST(...))
        # 首先尝试匹配最外层函数
        outer_func_pattern = r'([A-Za-z0-9_]+)\s*\((.*)\)'
        outer_match = re.search(outer_func_pattern, field_name, re.IGNORECASE | re.DOTALL)
        if outer_match:
            inner_expr = outer_match.group(2).strip()
            print(f"外层函数内表达式: {inner_expr}")
            
            # 然后尝试匹配内层CAST函数
            inner_cast_pattern = r'CAST\s*\(\s*([^()]+?)\s+AS\s+'
            inner_cast_match = re.search(inner_cast_pattern, inner_expr, re.IGNORECASE)
            if inner_cast_match:
                field_name = inner_cast_match.group(1).strip()
                print(f"从嵌套CAST提取字段: {field_name}")
                return field_name
        
        # 如果没有匹配到复杂表达式，返回原始字段名
        # 移除任何括号和函数名
        simple_field_pattern = r'[^(),\s]+'
        simple_fields = re.findall(simple_field_pattern, field_name)
        if simple_fields:
            # 过滤掉常见的SQL关键字和函数名
            keywords = ['select', 'from', 'where', 'group', 'order', 'by', 'having', 
                       'avg', 'sum', 'count', 'min', 'max', 'cast', 'as', 'and', 'or']
            filtered_fields = [f for f in simple_fields if f.lower() not in keywords]
            if filtered_fields:
                field_name = filtered_fields[0]
                print(f"提取简单字段名: {field_name}")
        
        return field_name.strip()
    
    def _extract_aliases(self, sql: str) -> Dict[str, str]:
        """提取SQL中的表别名"""
        # 匹配 "table AS alias" 或 "table alias" 格式
        alias_pattern = r'([a-zA-Z0-9_]+)\s+(?:AS\s+)?([a-zA-Z0-9_]+)'
        
        # 在FROM和JOIN子句中查找
        from_clause = re.search(r'FROM\s+(.*?)(?:WHERE|GROUP BY|ORDER BY|LIMIT|$)', sql, re.IGNORECASE | re.DOTALL)
        
        if not from_clause:
            return {}
            
        aliases = {}
        matches = re.findall(alias_pattern, from_clause.group(1), re.IGNORECASE)
        
        for match in matches:
            table, alias = match
            aliases[alias] = table
            
        return aliases
    
    def _check_condition_applied(self, sql: str, table: str, condition: str) -> bool:
        """
        检查SQL中是否已应用了指定的过滤条件
        """
        # 简化实现：检查WHERE子句中是否包含过滤条件
        where_pattern = r'WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|$)'
        where_match = re.search(where_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not where_match:
            return False
            
        where_clause = where_match.group(1)
        
        # 检查条件是否已包含在WHERE子句中
        # 这是一个简化的检查，实际应用中可能需要更复杂的语义分析
        condition_normalized = re.sub(r'\s+', ' ', condition.lower())
        where_normalized = re.sub(r'\s+', ' ', where_clause.lower())
        
        return condition_normalized in where_normalized
    
    def _apply_missing_conditions(self, sql: str, missing_conditions: List[Tuple[str, str]]) -> Optional[str]:
        """
        尝试修正SQL，添加缺失的过滤条件
        """
        try:
            # 检查SQL是否有WHERE子句
            where_exists = re.search(r'\bWHERE\b', sql, re.IGNORECASE)
            
            for table, condition in missing_conditions:
                if where_exists:
                    # 如果已有WHERE子句，添加AND条件
                    sql = re.sub(r'(WHERE\s+.*?)(\s+(?:GROUP BY|ORDER BY|LIMIT|$))', 
                                f'\\1 AND {condition}\\2', 
                                sql, 
                                flags=re.IGNORECASE | re.DOTALL)
                    where_exists = True  # 确保下一个条件也使用AND
                else:
                    # 如果没有WHERE子句，添加WHERE条件
                    sql = re.sub(r'(FROM\s+.*?)(\s+(?:GROUP BY|ORDER BY|LIMIT|$))', 
                                f'\\1 WHERE {condition}\\2', 
                                sql, 
                                flags=re.IGNORECASE | re.DOTALL)
                    where_exists = True  # 下一个条件需要使用AND
            
            return sql
        except Exception as e:
            print(f"应用过滤条件时出错: {str(e)}")
            return None