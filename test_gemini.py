import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. 强制配置代理 (必须和你 VPN 一致)
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 2. 加载 API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 错误：找不到 API Key，请检查 .env 文件")
else:
    print(f"✅ 找到 API Key: {api_key[:5]}...")
    genai.configure(api_key=api_key)

    print("\n🔍 正在询问 Google 有哪些模型可用...")
    
    try:
        # 列出所有支持的模型
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"👉 发现模型: {m.name}")
        
        print("\n--------------------------------")
        print("✅ 如果你看到了上面的列表，说明连接完全正常！")
        print("请把其中一个名字（比如 models/gemini-1.5-flash）复制到你的 Django 代码里。")

    except Exception as e:
        print(f"\n❌ 连接失败，报错信息如下：")
        print(e)