import aiohttp
import asyncio

async def test_deepseek_api(api_key: str):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": "Hello, this is a test message."
            }
        ],
        "stream": False
    }
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            print("正在测试 API 连接...")
            async with session.post(url, headers=headers, json=payload) as response:
                print(f"状态码: {response.status}")
                print(f"响应头: {response.headers}")
                
                if response.status == 200:
                    result = await response.json()
                    print("\nAPI 连接成功!")
                    print("响应内容:", result)
                else:
                    error_text = await response.text()
                    print("\nAPI 连接失败!")
                    print("错误信息:", error_text)
                    
    except Exception as e:
        print("\n发生错误:")
        print(str(e))

if __name__ == "__main__":
    api_key = "sk-073ca480b9184dcf9e1be31f805a356b"  # 你的 API key
    asyncio.run(test_deepseek_api(api_key))