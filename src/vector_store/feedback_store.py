from typing import List, Dict
import json
from pathlib import Path
import os
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

class FeedbackVectorStore:
    def __init__(self):
        print("正在加载本地模型...")
        model_path = Path(__file__).parent.parent / 'models' / 'text2vec-base-chinese'
        try:
            self.model = SentenceTransformer(str(model_path))
            print("成功加载本地模型")
        except Exception as e:
            print(f"模型加载失败: {str(e)}")
            raise
        self.index = None
        self.feedback_data = []
        self.initialize_store()

    def initialize_store(self):
        print("初始化向量数据库...")
        feedback_path = Path(__file__).parent.parent.parent / 'feedback' / 'feedback_data.json'
        
        with open(feedback_path, 'r', encoding='utf-8') as f:
            self.feedback_data = json.load(f)
        
        # 生成查询的向量表示
        queries = [item['query'] for item in self.feedback_data]
        embeddings = self.model.encode(queries)
        
        # 初始化 FAISS 索引
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        print(f"向量数据库初始化完成，包含 {len(self.feedback_data)} 条记录")

    def find_similar_examples(self, query: str, top_k: int = 5) -> List[Dict]:
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), top_k)
        similar_examples = []
        for idx in indices[0]:
            if idx < len(self.feedback_data):
                similar_examples.append(self.feedback_data[idx])
        
        return similar_examples