from fastapi import APIRouter, Depends, HTTPException, Body
import json
import os
import aiohttp
from ..utils.auth import verify_token
from .models import LLMConfig

router = APIRouter(tags=["LLM配置"])

# LLM API配置文件路径常量
LLM_CONFIG_FILE = "config\\llm_config.json"
os.makedirs(os.path.dirname(LLM_CONFIG_FILE), exist_ok=True)

# 默认LLM配置
default_llm_config = {
    "api_url": "https://api.deepseek.com/v1/chat/completions",
    "api_key": "",  # 移除硬编码的API密钥
    "model_name": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.95,
    "timeout": 60
}

@router.get("/llm/config", dependencies=[Depends(verify_token)])
async def get_llm_config():
    """获取大语言模型API配置"""
    try:
        # 如果配置文件不存在，返回默认配置
        if not os.path.exists(LLM_CONFIG_FILE):
            print(f"LLM配置文件不存在: {LLM_CONFIG_FILE}，返回默认配置")
            return {
                "status": "success", 
                "data": default_llm_config,
                "message": "使用默认配置"
            }
        
        # 读取配置文件
        with open(LLM_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"成功从 {LLM_CONFIG_FILE} 读取LLM配置")
        
        return {"status": "success", "data": config}
    except Exception as e:
        print(f"获取LLM配置失败: {str(e)}")
        # 出错时也返回默认配置
        return {
            "status": "success", 
            "data": default_llm_config,
            "message": f"读取配置失败，使用默认配置: {str(e)}"
        }

@router.post("/llm/config", dependencies=[Depends(verify_token)])
async def save_llm_config(config: LLMConfig):
    """保存大语言模型API配置"""
    try:
        # 保存配置到文件
        config_dir = os.path.dirname(LLM_CONFIG_FILE)
        print(f"确保配置目录存在: {config_dir}")
        os.makedirs(config_dir, exist_ok=True)  # 确保目录存在
        
        config_data = config.dict()
        print(f"准备保存的配置数据: {config_data}")
        
        # 使用绝对路径并确保文件可写
        print(f"正在写入配置文件: {LLM_CONFIG_FILE}")
        with open(LLM_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        # 更新当前运行的模型配置
        from ..main import query_model
        query_model.api_url = config.api_url
        query_model.api_key = config.api_key
        query_model.model_params = {
            "model": config.model_name,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p
        }
        
        print(f"LLM配置已成功保存到: {LLM_CONFIG_FILE}")
        # 确保返回正确的响应格式
        return {"status": "success", "message": "LLM API配置保存成功"}
    except Exception as e:
        error_msg = f"保存LLM配置失败: {str(e)}"
        print(error_msg)
        # 确保返回错误时也使用正确的响应格式
        return {"status": "error", "message": error_msg}

@router.post("/llm/test-connection", dependencies=[Depends(verify_token)])
async def test_llm_connection(config: LLMConfig):
    """测试LLM API连接"""
    try:
        print(f"测试LLM连接: {config.api_url}")
        print(f"使用API密钥: {config.api_key[:5]}...{config.api_key[-5:]}")
        
        # 使用aiohttp进行异步请求，与QueryModel中使用的方式保持一致
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.api_key}"
            }
            
            data = {
                "model": config.model_name,
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": config.temperature,
                "max_tokens": 10
            }
            
            print(f"发送测试请求到: {config.api_url}")
            print(f"请求数据: {data}")
            
            async with session.post(
                config.api_url,
                headers=headers,
                json=data,
                timeout=config.timeout
            ) as response:
                response_text = await response.text()
                status_code = response.status
                print(f"API响应状态码: {status_code}")
                print(f"API响应内容: {response_text[:200]}...")
                
                if status_code == 200:
                    return {"status": "success", "message": "LLM API连接成功"}
                else:
                    return {"status": "error", "message": f"LLM API连接失败: {response_text}"}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"LLM API连接测试异常: {str(e)}")
        print(f"错误详情: {error_detail}")
        return {"status": "error", "message": f"LLM API连接测试失败: {str(e)}"}