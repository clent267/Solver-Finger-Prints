# 🚀 Unified Solver - Quick Reference Card

## Installation (5 minutes)

```bash
# 1. Add files to GitHub repo
cp unified_solver.py main.py
cp arkose.js webgl.json decrypt_bda.py decrypt_tguess.py .
cp requirements.txt .
cp Dockerfile-unified Dockerfile

# 2. Push to GitHub
git add .
git commit -m "Unified FunCaptcha solver"
git push

# 3. Deploy on Render
# Go to render.com → New Web Service → Connect GitHub
# Plan: Standard ($12/month)
```

## 🎯 API Quick Calls

### Health Check
```bash
curl https://solver-xxxx.onrender.com/health
```

### Extract Blob Only
```bash
curl -X POST https://solver-xxxx.onrender.com/extract/blob \
  -H "Content-Type: application/json" \
  -d '{"preset": "roblox_login"}'
```

### ⭐ Unified: Extract + Solve (Recommended)
```bash
curl -X POST https://solver-xxxx.onrender.com/unified/solve \
  -H "Content-Type: application/json" \
  -d '{"preset": "roblox_login"}'
```

### Get Result
```bash
curl https://solver-xxxx.onrender.com/solve/status/TASK_ID
```

### Stats
```bash
curl https://solver-xxxx.onrender.com/stats
```

## 🐍 Python 5-Liner

```python
import requests, time

solver = "https://solver-xxxx.onrender.com"
task = requests.post(f"{solver}/unified/solve", json={"preset": "roblox_login"}).json()
while True:
    r = requests.get(f"{solver}/solve/status/{task['task_id']}").json()
    if r.get("status") == "completed": print(f"✅ {r['token']}"); break
    time.sleep(1)
```

## 📋 Request Templates

### Template 1: Simple Solve
```json
{
  "preset": "roblox_login"
}
```

### Template 2: With Proxy
```json
{
  "preset": "roblox_login",
  "proxy": "http://user:pass@host:port"
}
```

### Template 3: With Suppressed Challenge
```json
{
  "preset": "roblox_login",
  "has_suppressed": true,
  "suppressed_challenge": {
    "instruction": "Click on the car",
    "tiles": [
      {"image": "base64_data_1"},
      {"image": "base64_data_2"},
      {"image": "base64_data_3"},
      {"image": "base64_data_4"},
      {"image": "base64_data_5"},
      {"image": "base64_data_6"}
    ]
  }
}
```

### Template 4: With PoW Challenge
```json
{
  "preset": "roblox_login",
  "has_pow": true,
  "pow_challenge": {
    "seed": "challenge_seed",
    "difficulty": 32000
  }
}
```

## ✅ Response Formats

### Success (Solving)
```json
{
  "success": true,
  "task_id": "a1b2c3d4e5f6...",
  "blob": "token_data_here",
  "status": "solving"
}
```

### Processing Status
```json
{
  "success": true,
  "status": "processing"
}
```

### Completed (Regular)
```json
{
  "success": true,
  "status": "completed",
  "token": "solved_token_here"
}
```

### Completed (With Suppressed)
```json
{
  "success": true,
  "status": "completed",
  "token": "solved_token",
  "suppressed_answer": "3"
}
```

### Completed (With PoW)
```json
{
  "success": true,
  "status": "completed",
  "token": "solved_token",
  "pow_solution": "seed123456"
}
```

## 🔄 Polling Pattern

```python
import requests
import time

SOLVER = "https://solver-xxxx.onrender.com"
MAX_WAIT = 60

# Create task
task = requests.post(
    f"{SOLVER}/unified/solve",
    json={"preset": "roblox_login"}
).json()

task_id = task["task_id"]
start = time.time()

# Poll until done
while (time.time() - start) < MAX_WAIT:
    result = requests.get(
        f"{SOLVER}/solve/status/{task_id}"
    ).json()
    
    if result["status"] == "completed":
        token = result["token"]
        print(f"✅ Token: {token}")
        break
    
    print(f"⏳ Waiting... ({int(time.time() - start)}s)")
    time.sleep(1)
else:
    print("❌ Timeout")
```

## 🔑 Sitekeys Reference

```
Roblox Login:    476068BF-9607-4799-B53D-966BE98E2B81
Roblox Register: A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F
```

## 📊 Endpoint Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/extract/blob` | POST | Extract blob only |
| `/solve/create` | POST | Create solve task |
| `/solve/status/{id}` | GET | Check status |
| `/unified/solve` | POST | Extract + solve ⭐ |
| `/stats` | GET | Get statistics |
| `/funcaptcha/createTask` | POST | Legacy compat |
| `/funcaptcha/getTask` | POST | Legacy compat |

## 🚀 Common Workflows

### Workflow 1: Fast Solve (Recommended)
```
POST /unified/solve
    ↓
GET /solve/status/{task_id} (poll)
    ↓
✅ Token ready
```

### Workflow 2: Manual Blob Extract
```
POST /extract/blob
    ↓ (get blob)
POST /solve/create (with blob)
    ↓
GET /solve/status/{task_id} (poll)
    ↓
✅ Token ready
```

### Workflow 3: Suppressed Captcha
```
POST /unified/solve (has_suppressed: true)
    ↓
GET /solve/status/{task_id} (poll)
    ↓
✅ Token + suppressed_answer ready
```

### Workflow 4: With PoW
```
POST /unified/solve (has_pow: true)
    ↓
GET /solve/status/{task_id} (poll)
    ↓
✅ Token + pow_solution ready
```

## 🔧 Configuration

### Presets
```python
"roblox_login"      # Auto-extract + solve
"roblox_register"   # Auto-extract + solve
```

### Optional Parameters
```python
proxy: "http://proxy:port"           # Route through proxy
has_suppressed: true                 # Has suppressed challenge
suppressed_challenge: {...}          # Challenge data
has_pow: true                        # Has PoW challenge
pow_challenge: {...}                 # PoW data
```

## 📈 Performance Targets

| Operation | Target Time | Max Time |
|-----------|------------|----------|
| Extract blob | 1-2s | 5s |
| Regular solve | 2-5s | 30s |
| Suppressed solve | 5-30s | 60s |
| PoW solve | 1-5s | 30s |

## ❌ Error Codes

```
"success": false
"error": "No sitekey provided"       → Add sitekey or preset
"error": "Failed to extract blob"    → Arkose API error
"error": "Task not found"            → Invalid task_id
"error": "Status 429"                → Rate limited (use proxy)
"error": "Status 503"                → Service unavailable
```

## 🔐 Security Tips

1. **Use proxy** to avoid rate limiting
2. **Change User-Agent** regularly
3. **Space out requests** (1-2s delay)
4. **Monitor stats** (/stats endpoint)
5. **Rotate residential proxies**

## 📞 Troubleshooting

**502 Bad Gateway**
- Solver crashed → Check Render logs
- Wait 30-60 seconds for restart

**Timeout**
- Increase MAX_WAIT to 120
- Check proxy connection
- Try different sitekey preset

**Token Invalid**
- Tokens expire after 5-10 minutes
- Re-solve immediately after extraction
- Verify correct sitekey

**Rate Limited (429)**
- Add proxy parameter
- Space requests 1-2 seconds apart
- Use different proxy IP

## 📊 Monitoring

```bash
# Health
curl https://solver-xxxx.onrender.com/health

# Stats
curl https://solver-xxxx.onrender.com/stats

# Response:
# {
#   "solved": 100,
#   "failed": 2,
#   "suppressed_solved": 15,
#   "pow_solved": 8,
#   "errors": 0
# }
```

## 💡 Pro Tips

1. **Batch solving**: Create 10 tasks, poll all together
2. **Caching**: Cache blobs for same sitekey (5 min TTL)
3. **Threading**: Use concurrent.futures for parallel solving
4. **Logging**: Log task_ids and timestamps for analytics
5. **Fallback**: Have backup solver URL if primary fails

## 🎯 Complete Example

```python
#!/usr/bin/env python3
import requests
import time

class RobloxSolver:
    def __init__(self, url):
        self.url = url.rstrip('/')
    
    def solve(self, preset="roblox_login"):
        # Create task
        task = requests.post(
            f"{self.url}/unified/solve",
            json={"preset": preset}
        ).json()
        
        if not task.get("success"):
            return None
        
        # Poll result
        for _ in range(60):
            result = requests.get(
                f"{self.url}/solve/status/{task['task_id']}"
            ).json()
            
            if result.get("status") == "completed":
                return result.get("token")
            
            time.sleep(1)
        
        return None

# Usage
solver = RobloxSolver("https://solver-xxxx.onrender.com")
token = solver.solve("roblox_login")
print(f"Token: {token}")
```

---

**Everything you need on one page!** 📋

Copy-paste ready code examples included ✨
