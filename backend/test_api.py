import requests

BASE_URL = "http://127.0.0.1:8000"
# 项目级 API Key —— 从 Notify Hub 前端 Dashboard 的项目菜单「复制 API Key」获取
API_KEY = "PASTE-PROJECT-API-KEY-HERE"

def test_push_only():
    print(f"Testing Push API against {BASE_URL}...")
    
    headers = {
        "X-Project-Key": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Payload without project_name — 项目由 X-Project-Key 头决定
    payload = {
        "title": "Push Test",
        "content": "This is a notification sent using ONLY the Project API Key.",
        "level": "info"
    }
    
    print("\n[1] Sending Notification...")
    try:
        resp = requests.post(f"{BASE_URL}/api/notify", json=payload, headers=headers)
        if resp.status_code == 200:
            print(f"SUCCESS: Notification sent.")
            print(f"Response: {resp.json()}")
        else:
            print(f"FAILED: Status {resp.status_code}")
            print(f"Body: {resp.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_push_only()
