import httpx
import os

headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json",
    "Referer": "https://github.com/cabovidio",
    "X-Title": "TestBot"
}

data = {
    "model": "mistralai/mixtral-8x7b-instruct",  # ✅ available and powerful
    "messages": [{"role": "user", "content": "Say hi in JSON like {\"message\": \"hello\"}"}],
    "temperature": 0.2
}

response = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

print("STATUS:", response.status_code)
print("RESPONSE:", response.text)
