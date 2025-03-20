from typing import Dict, Any, Optional
import uuid

class QueryContext:
    """
    查询上下文管理类
    用于管理和存储查询会话的上下文信息
    """
    def __init__(self):
        """
        初始化查询上下文管理器
        创建一个空的上下文存储字典
        """
        self.context_store: Dict[str, Dict[str, Any]] = {}

    def create_context(self) -> str:
        """
        创建新的上下文
        返回: 新创建的上下文ID
        """
        context_id = str(uuid.uuid4())
        self.context_store[context_id] = {
            'history': [],      # 存储历史记录
            'parameters': {},   # 存储参数
            'state': 'initialized'  # 初始状态
        }
        return context_id

    def update_context(self, context_id: str, data: Dict[str, Any]) -> None:
        """
        更新指定上下文的信息
        参数:
            context_id: 上下文ID
            data: 要更新的数据
        """
        if context_id in self.context_store:
            self.context_store[context_id]['history'].append(data)
            self.context_store[context_id]['state'] = data.get('state', 'updated')

    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定上下文的信息
        参数:
            context_id: 上下文ID
        返回:
            如果存在返回上下文信息，否则返回None
        """
        return self.context_store.get(context_id)