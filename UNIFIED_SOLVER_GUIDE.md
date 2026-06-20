# 🚀 Unified Roblox FunCaptcha Solver v2.0 for Render

All-in-one service that:
- ✅ **Extracts blobs** from Arkose Labs
- ✅ **Solves regular captchas**
- ✅ **Solves suppressed captchas** (image recognition required)
- ✅ **Solves PoW challenges** (Proof of Work)
- ✅ **Runs 24/7 on Render**

## 🎯 Features

| Feature | Status | Notes |
|---------|--------|-------|
| **Blob Extraction** | ✅ Built-in | No need for separate tool |
| **Regular Captcha** | ✅ Full support | Roblox login/register |
| **Suppressed Captcha** | ✅ Basic solver | Integrate image recognition for better results |
| **PoW Solving** | ✅ Built-in | SHA256-based proof of work |
| **Async Processing** | ✅ Threaded | Non-blocking solving |
| **Proxy Support** | ✅ Full | For all requests |
| **Statistics** | ✅ Real-time | Track solved/failed/errors |

## 📝 API Endpoints

### 1. Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "service": "unified-funcaptcha-solver",
  "version": "2.0.0",
  "stats": {
    "solved": 42,
    "suppressed_solved": 5,
    "pow_solved": 3,
    "errors": 0
  }
}
```

### 2. Extract Blob Only
```bash
POST /extract/blob

Request:
{
  "sitekey": "476068BF-9607-4799-B53D-966BE98E2B81",
  "preset": "roblox_login",
  "proxy": "http://proxy:port"
}

Response:
{
  "success": true,
  "blob": "eyJjdG1fdmVyc2lvbiI6IjUuNS4wIi...",
  "public_key": "476068BF-9607-4799-B53D-966BE98E2B81",
  "timestamp": 1234567890
}
```

### 3. Solve Regular Captcha (Manual Blob)
```bash
POST /solve/create

Request:
{
  "preset": "roblox_login",
  "blob": "blob_data_here",
  "has_suppressed": false,
  "has_pow": false,
  "proxy": "optional_proxy"
}

Response:
{
  "success": true,
  "task_id": "a1b2c3d4...",
  "status": "solving"
}
```

### 4. Check Task Status
```bash
GET /solve/status/{task_id}

Response (Processing):
{
  "success": true,
  "status": "processing"
}

Response (Completed):
{
  "success": true,
  "status": "completed",
  "token": "solved_token_here",
  "suppressed_answer": "optional_if_suppressed",
  "pow_solution": "optional_if_pow"
}
```

### 5. ⭐ UNIFIED: Extract + Solve (All-in-One)
```bash
POST /unified/solve

Request:
{
  "preset": "roblox_login",
  "has_suppressed": false,
  "has_pow": false,
  "proxy": "optional"
}

Response:
{
  "success": true,
  "task_id": "uuid_here",
  "blob": "blob_data",
  "status": "solving"
}

# Then check with: GET /solve/status/{task_id}
```

### 6. Solve With Suppressed Challenge
```bash
POST /solve/create

Request:
{
  "preset": "roblox_login",
  "blob": "blob_data",
  "has_suppressed": true,
  "suppressed_challenge": {
    "instruction": "Click on the tile that matches...",
    "tiles": [
      {"image": "tile1_data"},
      {"image": "tile2_data"}
    ]
  }
}

Response:
{
  "success": true,
  "task_id": "uuid_here"
}

# Status will include suppressed_answer when completed
```

### 7. Solve With PoW Challenge
```bash
POST /solve/create

Request:
{
  "preset": "roblox_login",
  "blob": "blob_data",
  "has_pow": true,
  "pow_challenge": {
    "seed": "challenge_seed_data",
    "difficulty": 32000
  }
}

Response:
{
  "success": true,
  "task_id": "uuid_here"
}

# Status will include pow_solution when completed
```

### 8. Statistics
```bash
GET /stats

Response:
{
  "solved": 100,
  "failed": 2,
  "suppressed_solved": 15,
  "pow_solved": 8,
  "errors": 0,
  "uptime": 1234567890
}
```

### 9. Legacy Endpoints (Backward Compatible)
```bash
# Old createTask endpoint still works
POST /funcaptcha/createTask
POST /funcaptcha/getTask
```

## 🐍 Python Examples

### Simple: Extract + Solve
```python
import requests
import time

SOLVER = "https://your-solver.onrender.com"

# One request extracts blob AND starts solving!
response = requests.post(f"{SOLVER}/unified/solve", json={
    "preset": "roblox_login"
}).json()

task_id = response["task_id"]
print(f"Task: {task_id}")
print(f"Blob: {response['blob']}")

# Poll for result
while True:
    result = requests.get(f"{SOLVER}/solve/status/{task_id}").json()
    
    if result["status"] == "completed":
        print(f"✅ Token: {result['token']}")
        break
    
    print("⏳ Processing...")
    time.sleep(1)
```

### With Suppressed Challenge
```python
import requests
import time

SOLVER = "https://your-solver.onrender.com"

# Extract blob first
blob = requests.post(f"{SOLVER}/extract/blob", json={
    "preset": "roblox_login"
}).json()["blob"]

# Solve with suppressed challenge
response = requests.post(f"{SOLVER}/solve/create", json={
    "preset": "roblox_login",
    "blob": blob,
    "has_suppressed": True,
    "suppressed_challenge": {
        "instruction": "Click on the car",
        "tiles": [
            {"image": "base64_image_data_1"},
            {"image": "base64_image_data_2"},
            {"image": "base64_image_data_3"},
            {"image": "base64_image_data_4"},
            {"image": "base64_image_data_5"},
            {"image": "base64_image_data_6"}
        ]
    }
}).json()

task_id = response["task_id"]

# Poll result
while True:
    result = requests.get(f"{SOLVER}/solve/status/{task_id}").json()
    
    if result["status"] == "completed":
        print(f"✅ Token: {result['token']}")
        print(f"Suppressed Answer: {result['suppressed_answer']}")
        break
    
    time.sleep(1)
```

### With Proxy Support
```python
import requests

SOLVER = "https://your-solver.onrender.com"
PROXY = "http://user:pass@proxy:port"

response = requests.post(f"{SOLVER}/unified/solve", json={
    "preset": "roblox_login",
    "proxy": PROXY
}).json()

print(f"Task: {response['task_id']}")
```

### With PoW Challenge
```python
import requests
import time

SOLVER = "https://your-solver.onrender.com"

blob = requests.post(f"{SOLVER}/extract/blob", json={
    "preset": "roblox_login"
}).json()["blob"]

response = requests.post(f"{SOLVER}/solve/create", json={
    "preset": "roblox_login",
    "blob": blob,
    "has_pow": True,
    "pow_challenge": {
        "seed": "pow_seed_data",
        "difficulty": 32000
    }
}).json()

task_id = response["task_id"]

# Poll result
while True:
    result = requests.get(f"{SOLVER}/solve/status/{task_id}").json()
    
    if result["status"] == "completed":
        print(f"✅ Token: {result['token']}")
        print(f"PoW Solution: {result['pow_solution']}")
        break
    
    time.sleep(1)
```

### Complete Solution Class
```python
import requests
import time
from typing import Optional

class RobloxUnifiedSolver:
    """Complete Roblox solver using unified endpoint"""
    
    def __init__(self, solver_url: str, timeout: int = 60):
        self.solver_url = solver_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def solve(self, 
              preset: str = "roblox_login",
              has_suppressed: bool = False,
              suppressed_challenge: dict = None,
              has_pow: bool = False,
              pow_challenge: dict = None,
              proxy: Optional[str] = None) -> Optional[dict]:
        """
        Unified solve (extracts blob + solves in one call)
        
        Returns:
            {
                "token": "token_here",
                "suppressed_answer": "answer_if_suppressed",
                "pow_solution": "solution_if_pow",
                "blob": "blob_data"
            }
        """
        try:
            # Create solve task (auto-extracts blob)
            print(f"🔄 Solving {preset}...")
            
            create_data = {
                "preset": preset,
                "has_suppressed": has_suppressed,
                "has_pow": has_pow,
                "proxy": proxy
            }
            
            if suppressed_challenge:
                create_data["suppressed_challenge"] = suppressed_challenge
            if pow_challenge:
                create_data["pow_challenge"] = pow_challenge
            
            response = self.session.post(
                f"{self.solver_url}/unified/solve",
                json=create_data,
                timeout=10
            ).json()
            
            if not response.get("success"):
                print(f"❌ Failed to create task: {response.get('error')}")
                return None
            
            task_id = response["task_id"]
            blob = response.get("blob")
            print(f"📝 Task: {task_id}")
            print(f"🔗 Blob: {blob[:50]}..." if blob else "")
            
            # Poll for result
            start = time.time()
            while (time.time() - start) < self.timeout:
                result = self.session.get(
                    f"{self.solver_url}/solve/status/{task_id}",
                    timeout=10
                ).json()
                
                status = result.get("status")
                
                if status == "completed":
                    print(f"✅ Solved!")
                    return {
                        "token": result.get("token"),
                        "suppressed_answer": result.get("suppressed_answer"),
                        "pow_solution": result.get("pow_solution"),
                        "blob": blob
                    }
                
                print(f"⏳ Processing ({int(time.time() - start)}s)")
                time.sleep(1)
            
            print(f"❌ Timeout after {self.timeout}s")
            return None
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

# Usage
solver = RobloxUnifiedSolver("https://your-solver.onrender.com")

# Simple Roblox login
result = solver.solve(preset="roblox_login")
if result:
    print(f"Token: {result['token']}")

# With suppressed challenge
result = solver.solve(
    preset="roblox_login",
    has_suppressed=True,
    suppressed_challenge={
        "instruction": "Click on the car",
        "tiles": [...]  # image data
    }
)
if result:
    print(f"Token: {result['token']}")
    print(f"Answer: {result['suppressed_answer']}")
```

## 🚀 Deploy to Render

### Step 1: Prepare Files
```bash
# Copy these to your repo:
unified_solver.py          # Main solver
arkose.js                  # From uploaded files
webgl.json                 # From uploaded files
decrypt_bda.py             # From uploaded files
decrypt_tguess.py          # From uploaded files
requirements.txt           # Dependencies
Dockerfile                 # Container config (rename from Dockerfile-unified)
```

### Step 2: Deploy
1. Go to https://render.com/dashboard
2. New → Web Service
3. Connect GitHub repo
4. Set Plan: **Standard ($12/month)**
5. Environment Variables:
   ```
   PORT=8080
   FLASK_ENV=production
   PYTHONUNBUFFERED=1
   DEBUG=false
   ```
6. Deploy!

### Step 3: Test
```bash
SOLVER_URL="https://your-solver-xxxx.onrender.com"

# Health check
curl $SOLVER_URL/health

# Extract blob
curl -X POST $SOLVER_URL/extract/blob \
  -H "Content-Type: application/json" \
  -d '{"preset": "roblox_login"}'

# Unified solve
curl -X POST $SOLVER_URL/unified/solve \
  -H "Content-Type: application/json" \
  -d '{"preset": "roblox_login"}'
```

## ⚙️ Configuration

### Sitekeys
```python
ROBLOX_LOGIN_SITEKEY = "476068BF-9607-4799-B53D-966BE98E2B81"
ROBLOX_REGISTER_SITEKEY = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"
```

### Adjustable Parameters
- **Workers**: Change `--workers 4` in Dockerfile (increase for more load)
- **Timeout**: Change `--timeout 120` (increase for slow networks)
- **Threads**: Change `--threads 2` per worker

## 📊 Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **Blob Extraction** | ~1-2s | Depends on Arkose API |
| **Regular Solve** | ~2-5s | Async processing |
| **Suppressed Solve** | ~5-30s | Depends on image recognition |
| **PoW Solve** | ~1-5s | Depends on difficulty |
| **Concurrent Tasks** | 10+ | Limited by plan tier |

## 🔧 Integration with Image Recognition

For better suppressed captcha solving, integrate with:
- **XEvil** (0x80 API)
- **CapSolver** (capsolver.com)
- **OpenAI Vision** (GPT-4V)
- **Hugging Face** (free models)

Example with CapSolver:
```python
import requests

def solve_suppressed_with_capsolver(tiles: list, instruction: str, capsolver_key: str) -> str:
    """Use CapSolver for image recognition"""
    
    # Send first tile image to CapSolver
    response = requests.post(
        "https://api.capsolver.com/createTask",
        json={
            "clientKey": capsolver_key,
            "task": {
                "type": "ImageToTextTask",
                "body": tiles[0]["image"],  # base64 encoded
                "phrase": instruction  # "Click on the car"
            }
        }
    ).json()
    
    task_id = response["taskId"]
    
    # Poll for result
    while True:
        result = requests.post(
            "https://api.capsolver.com/getTaskResult",
            json={"clientKey": capsolver_key, "taskId": task_id}
        ).json()
        
        if result["status"] == "ready":
            return result["solution"]["text"]
        
        time.sleep(1)
```

Then modify `SuppressedSolver.solve_suppressed()` to call this function.

## 📈 Scaling Tips

### For High Traffic
```dockerfile
# In Dockerfile, increase workers:
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "8",          # ← Increase this
     "--worker-class", "gthread", \
     "--threads", "4",          # ← And this
     ...]
```

### Use Redis Cache (Optional)
```python
import redis

cache = redis.Redis(host='localhost', port=6379)

# Cache extracted blobs for 5 minutes
cache.setex(f"blob:{sitekey}", 300, blob)
```

### Database Logging
```python
# Store solving history for analytics
import sqlite3

db = sqlite3.connect('solver.db')
db.execute('INSERT INTO solves VALUES (?, ?, ?)', (task_id, status, timestamp))
```

## 🚨 Error Handling

### Common Issues

**502 Bad Gateway**
- Solver crashed → Check logs
- Dependency import error → Check requirements.txt
- arkose.js missing → Verify file exists

**Timeout**
- Network slow → Increase --timeout
- Arkose API down → Check status
- Too many concurrent tasks → Upgrade plan

**Token Invalid**
- Expired → Token has TTL, re-solve
- Wrong sitekey → Verify public_key
- Arkose rejected → Check fingerprints

## 📞 Support

- Logs: https://dashboard.render.com/[service]/logs
- Metrics: https://dashboard.render.com/[service]/metrics
- Health: GET `/health` endpoint
- Stats: GET `/stats` endpoint

---

**Your unified Roblox FunCaptcha solver is ready!** 🎉

All-in-one: Extract blob → Solve regular/suppressed → Solve PoW ✨
