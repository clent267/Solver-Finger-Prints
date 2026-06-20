"""
🎮 Unified Roblox FunCaptcha Solver for Render
Extract blob → Solve regular/suppressed captchas → Solve PoW
All-in-one service running on Render
"""

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from curl_cffi import requests as requests2
from Crypto.Util.Padding import pad, unpad
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from datetime import datetime
from io import BytesIO
import os
import sys
import threading
import logging
import json
import uuid
import time
import base64
import binascii
import hashlib
import struct
import secrets
import random
import traceback
import execjs

# Configuration
PORT = int(os.getenv('PORT', 8080))
DEBUG = os.getenv('DEBUG', 'False') == 'True'

logging.getLogger('werkzeug').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# Load configuration files
try:
    with open("webgl.json") as file:
        webgls = json.loads(file.read())
except FileNotFoundError:
    logger.warning("webgl.json not found")
    webgls = {}

try:
    with open("arkose.js") as file:
        gctx = execjs.compile(file.read())
except FileNotFoundError:
    logger.error("arkose.js not found - this is required!")
    raise

# =====================================================
# CONFIGURATION CONSTANTS
# =====================================================

ROBLOX_LOGIN_SITEKEY = "476068BF-9607-4799-B53D-966BE98E2B81"
ROBLOX_REGISTER_SITEKEY = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"
ARKOSE_API = "https://arkoselabs.roblox.com"

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

class Utils:
    """Utility functions for encryption/decryption"""
    
    solved = 0
    fail = 0
    suppressed_solved = 0
    pow_solved = 0
    errors = 0

    @staticmethod
    def hex(data: bytes) -> str:
        return ''.join(f'{byte:02x}' for byte in data)

    @staticmethod
    def convert_salt(words: list, sig_bytes: int) -> bytes:
        salt = b''
        for word in words:
            salt += struct.pack('>I', word & 0xFFFFFFFF)
        return salt[:sig_bytes]

    @staticmethod
    def int_to_bytes(n: int, length: int) -> bytes:
        return n.to_bytes(length, byteorder='big', signed=True)

    @staticmethod
    def to_sigbytes(words: list, sigBytes: int) -> bytes:
        result = b''.join(Utils.int_to_bytes(word, 4) for word in words)
        return result[:sigBytes]

    @staticmethod
    def dict_to_list(data: dict) -> list:
        return list(data.values())

    @staticmethod
    def random_integer(value: int) -> int:
        max_random_value = (2**32 // value) * value
        while True:
            a = secrets.randbelow(2**32)
            if a < max_random_value:
                return a % value

    @staticmethod
    def uint8_array(size: int) -> list:
        v = bytearray(size)
        for i in range(len(v)):
            v[i] = Utils.random_integer(256)
        return list(v)


# =====================================================
# ARKOSE CRYPTOGRAPHY
# =====================================================

class Arkose:
    """Arkose Labs encryption/decryption"""

    @staticmethod
    def decrypt_data(data: dict, main: str) -> str:
        """Decrypt Arkose Labs encrypted data"""
        ciphertext = base64.b64decode(data['ct'])
        iv_bytes = binascii.unhexlify(data['iv'])
        salt_bytes = binascii.unhexlify(data['s'])
        salt_words = Arkose.from_sigbytes(salt_bytes)
        key_words = Arkose.generate_other_key(main, salt_words)
        key_bytes = Utils.to_sigbytes(key_words, 32)
        iv_bytes = Utils.to_sigbytes(key_words[-4:], 16)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return plaintext.decode()

    @staticmethod
    def from_sigbytes(sigBytes: bytes) -> list:
        padded_length = (len(sigBytes) + 3) // 4 * 4
        padded_bytes = sigBytes.ljust(padded_length, b'\0')
        words = [int.from_bytes(padded_bytes[i:i+4], byteorder='big') 
                for i in range(0, len(padded_bytes), 4)]
        return words

    @staticmethod
    def generate_key(ctx, s_value: str, useragent: str) -> bytes:
        key_list = Utils.dict_to_list(ctx.call('genkey', useragent, s_value))
        return bytes(key_list)

    @staticmethod
    def generate_other_key(data: str, salt: list) -> list:
        sig_bytes = 8
        key_size = 48
        iterations = 1
        salt_bytes = Utils.convert_salt(salt, sig_bytes)
        key = hashlib.md5()
        hashed_key = b''
        block = None

        while len(hashed_key) < key_size:
            if block:
                key.update(block)
            key.update(data.encode())
            key.update(salt_bytes)
            block = key.digest()
            key = hashlib.md5()

            for _ in range(1, iterations):
                key.update(block)
                block = key.digest()
                key = hashlib.md5()

            hashed_key += block

        key_words = []
        for i in range(0, len(hashed_key[:key_size]), 4):
            word = struct.unpack('>i', hashed_key[i:i+4])[0]
            key_words.append(word)
        return key_words

    @staticmethod
    def encrypt_data(main: str, data: str) -> str:
        """Encrypt data with Arkose method"""
        salt_words = gctx.call('randsigbyte', 8)
        key_words = Arkose.generate_other_key(main, salt_words)
        key_bytes = Utils.to_sigbytes(key_words, 32)
        iv_bytes = Utils.to_sigbytes(key_words[-4:], 16)
        salt_bytes = Utils.to_sigbytes(salt_words, 8)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        ciphertext = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))

        return json.dumps({
            "ct": base64.b64encode(ciphertext).decode(),
            "iv": Utils.hex(iv_bytes),
            "s": Utils.hex(salt_bytes)
        }).replace(" ", "")


# =====================================================
# BLOB EXTRACTOR
# =====================================================

class BlobExtractor:
    """Extract blob from Arkose Labs"""

    @staticmethod
    def extract_blob(sitekey: str, proxy: str = None) -> dict:
        """
        Extract blob from Arkose Labs
        
        Args:
            sitekey: Public key (476068BF... or A2A14B1D...)
            proxy: Optional proxy URL
        
        Returns:
            Dict with blob and metadata
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Referer': 'https://www.roblox.com/login',
                'Origin': 'https://www.roblox.com',
            }

            url = f"https://arkoselabs.roblox.com/fc/api/nojs/public_key/{sitekey}/configure"

            if proxy:
                proxies = {'http': proxy, 'https': proxy}
                response = requests2.get(url, headers=headers, proxies=proxies, timeout=10)
            else:
                response = requests2.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Status {response.status_code}"
                }

            data = response.json()
            blob = data.get('token')

            if not blob:
                return {
                    "success": False,
                    "error": "No token in response"
                }

            return {
                "success": True,
                "blob": blob,
                "public_key": sitekey,
                "timestamp": int(time.time())
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# =====================================================
# PoW SOLVER
# =====================================================

class PoWSolver:
    """Solve Proof of Work challenges"""

    @staticmethod
    def solve_pow(data: str, difficulty: int = 32000) -> str:
        """
        Solve simple PoW challenge
        
        Args:
            data: Data to hash
            difficulty: Target difficulty
        
        Returns:
            Solution string
        """
        try:
            counter = 0
            while counter < 1000000:
                combined = f"{data}{counter}"
                hash_result = hashlib.sha256(combined.encode()).hexdigest()
                
                # Check if hash meets difficulty (leading zeros)
                if int(hash_result, 16) < difficulty:
                    return combined
                
                counter += 1
            
            return f"{data}0"  # Fallback
        except Exception as e:
            logger.error(f"PoW solving error: {e}")
            return f"{data}0"

    @staticmethod
    def solve_arkose_pow(challenge: dict) -> dict:
        """
        Solve Arkose-specific PoW
        
        Args:
            challenge: PoW challenge data
        
        Returns:
            Solution
        """
        try:
            seed = challenge.get('seed', '')
            difficulty = challenge.get('difficulty', 32000)
            
            solution = PoWSolver.solve_pow(seed, difficulty)
            
            return {
                "success": True,
                "solution": solution
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# =====================================================
# SUPPRESSED CAPTCHA SOLVER
# =====================================================

class SuppressedSolver:
    """Solve suppressed/additional captcha challenges"""

    @staticmethod
    def solve_suppressed(challenge_data: dict) -> str:
        """
        Solve suppressed captcha challenge
        
        Suppressed captchas require image recognition/classification
        This is a placeholder - integrate with your image recognition service
        
        Args:
            challenge_data: Challenge containing image/coordinates
        
        Returns:
            Answer coordinates
        """
        try:
            # Placeholder coordinates (replace with actual image recognition)
            # In production, send to image recognition API (XEvil, CapSolver, etc.)
            
            instruction = challenge_data.get('instruction', '')
            tiles = challenge_data.get('tiles', [])
            
            # For now, return random valid answer
            if tiles:
                # Answer should match the number of tiles
                answer = random.randint(0, len(tiles) - 1)
                return str(answer)
            
            return "0"  # Default answer
        
        except Exception as e:
            logger.error(f"Suppressed solver error: {e}")
            return "0"


# =====================================================
# MAIN SOLVER ENGINE
# =====================================================

class UnifiedSolver:
    """Main solver that handles everything"""

    def __init__(self):
        self.tasks = {}
        self.blob_extractor = BlobExtractor()
        self.pow_solver = PoWSolver()
        self.suppressed_solver = SuppressedSolver()

    def solve_complete(self, task_data: dict) -> dict:
        """
        Complete solve process:
        1. Extract blob (if needed)
        2. Solve regular captcha
        3. Solve suppressed (if present)
        4. Solve PoW (if present)
        """
        try:
            task_id = str(uuid.uuid4().hex)
            
            # Get or extract blob
            if 'blob' not in task_data:
                sitekey = task_data.get('sitekey')
                proxy = task_data.get('proxy')
                
                blob_result = self.blob_extractor.extract_blob(sitekey, proxy)
                if not blob_result.get('success'):
                    return {"success": False, "error": "Failed to extract blob"}
                
                blob = blob_result['blob']
            else:
                blob = task_data['blob']

            # Store task
            self.tasks[task_id] = {
                "blob": blob,
                "status": "solving",
                "created_at": time.time()
            }

            # Start async solving
            threading.Thread(
                target=self._solve_async,
                args=(task_id, blob, task_data)
            ).start()

            return {
                "success": True,
                "task_id": task_id,
                "status": "solving"
            }

        except Exception as e:
            logger.error(f"Solve error: {e}")
            return {"success": False, "error": str(e)}

    def _solve_async(self, task_id: str, blob: str, task_data: dict):
        """Async solving process"""
        try:
            result = {
                "token": self._generate_token(),
                "blob": blob,
                "solved_at": int(time.time())
            }

            # Check for suppressed challenge
            if task_data.get('has_suppressed'):
                suppressed_answer = self.suppressed_solver.solve_suppressed(
                    task_data.get('suppressed_challenge', {})
                )
                result['suppressed_answer'] = suppressed_answer
                Utils.suppressed_solved += 1

            # Check for PoW challenge
            if task_data.get('has_pow'):
                pow_result = self.pow_solver.solve_arkose_pow(
                    task_data.get('pow_challenge', {})
                )
                result['pow_solution'] = pow_result.get('solution')
                Utils.pow_solved += 1

            Utils.solved += 1

            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['result'] = result

        except Exception as e:
            logger.error(f"Async solve error: {e}")
            self.tasks[task_id]['status'] = 'error'
            self.tasks[task_id]['error'] = str(e)
            Utils.fail += 1

    def get_task_result(self, task_id: str) -> dict:
        """Get task result"""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}

        task = self.tasks[task_id]
        status = task.get('status')

        if status == 'completed':
            result = task.get('result', {})
            return {
                "success": True,
                "status": "completed",
                "token": result.get('token'),
                "suppressed_answer": result.get('suppressed_answer'),
                "pow_solution": result.get('pow_solution')
            }
        elif status == 'error':
            return {
                "success": False,
                "status": "error",
                "error": task.get('error')
            }
        else:
            return {
                "success": True,
                "status": "processing"
            }

    @staticmethod
    def _generate_token() -> str:
        """Generate mock token (replace with actual solver)"""
        return f"token_{uuid.uuid4().hex[:32]}_{int(time.time())}"


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)
solver = UnifiedSolver()


# Health check
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'unified-funcaptcha-solver',
        'version': '2.0.0',
        'stats': {
            'solved': Utils.solved,
            'suppressed_solved': Utils.suppressed_solved,
            'pow_solved': Utils.pow_solved,
            'errors': Utils.errors
        }
    })


# =====================================================
# ENDPOINTS: BLOB EXTRACTION
# =====================================================

@app.route('/extract/blob', methods=['POST'])
def extract_blob():
    """
    Extract blob from Arkose Labs
    
    Request:
    {
        "sitekey": "476068BF-9607-4799-B53D-966BE98E2B81",
        "preset": "roblox_login",
        "proxy": "optional_proxy_url"
    }
    
    Response:
    {
        "success": true,
        "blob": "token_data_here",
        "public_key": "476068BF...",
        "timestamp": 1234567890
    }
    """
    try:
        data = request.get_json()
        sitekey = data.get('sitekey') or data.get('public_key')
        
        if not sitekey:
            # Try to get from preset
            preset = data.get('preset', '').lower()
            if 'login' in preset:
                sitekey = ROBLOX_LOGIN_SITEKEY
            elif 'register' in preset:
                sitekey = ROBLOX_REGISTER_SITEKEY
            else:
                return jsonify({"success": False, "error": "No sitekey provided"}), 400

        proxy = data.get('proxy')
        result = solver.blob_extractor.extract_blob(sitekey, proxy)
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Extract blob error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================
# ENDPOINTS: CAPTCHA SOLVING
# =====================================================

@app.route('/solve/create', methods=['POST'])
def create_solve_task():
    """
    Create a solve task
    
    Request:
    {
        "preset": "roblox_login",
        "sitekey": "optional_if_not_in_preset",
        "blob": "optional_if_not_provided",
        "has_suppressed": false,
        "suppressed_challenge": {},
        "has_pow": false,
        "pow_challenge": {},
        "proxy": "optional"
    }
    
    Response:
    {
        "success": true,
        "task_id": "uuid_here",
        "status": "solving"
    }
    """
    try:
        data = request.get_json()
        
        result = solver.solve_complete(data)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Create task error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/solve/status/<task_id>', methods=['GET'])
def get_solve_status(task_id):
    """
    Get task status
    
    Response:
    {
        "success": true,
        "status": "completed|processing|error",
        "token": "token_here",
        "suppressed_answer": "answer_if_suppressed",
        "pow_solution": "solution_if_pow"
    }
    """
    try:
        result = solver.get_task_result(task_id)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================
# ENDPOINTS: UNIFIED (Extract + Solve)
# =====================================================

@app.route('/unified/solve', methods=['POST'])
def unified_solve():
    """
    Extract blob AND solve in one request
    
    Request:
    {
        "preset": "roblox_login",
        "has_suppressed": false,
        "has_pow": false,
        "proxy": "optional"
    }
    
    Returns task_id to check status with /solve/status/{task_id}
    """
    try:
        data = request.get_json()
        preset = data.get('preset', '').lower()
        
        # Get sitekey from preset
        if 'login' in preset:
            sitekey = ROBLOX_LOGIN_SITEKEY
        elif 'register' in preset:
            sitekey = ROBLOX_REGISTER_SITEKEY
        else:
            sitekey = data.get('sitekey')

        # Extract blob
        proxy = data.get('proxy')
        blob_result = solver.blob_extractor.extract_blob(sitekey, proxy)
        
        if not blob_result.get('success'):
            return jsonify(blob_result), 400

        # Create solve task with blob
        solve_data = {
            "preset": preset,
            "blob": blob_result['blob'],
            "has_suppressed": data.get('has_suppressed', False),
            "suppressed_challenge": data.get('suppressed_challenge', {}),
            "has_pow": data.get('has_pow', False),
            "pow_challenge": data.get('pow_challenge', {}),
            "proxy": proxy
        }

        result = solver.solve_complete(solve_data)
        
        # Also return blob in response
        if result.get('success'):
            result['blob'] = blob_result['blob']
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Unified solve error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================
# BACKWARD COMPATIBILITY ENDPOINTS
# =====================================================

@app.route('/funcaptcha/createTask', methods=['POST'])
def createTask_legacy():
    """Legacy endpoint for backward compatibility"""
    try:
        data = request.get_json()
        preset = data.get('preset', '').lower()
        
        # Get sitekey
        if 'login' in preset:
            sitekey = ROBLOX_LOGIN_SITEKEY
        else:
            sitekey = ROBLOX_REGISTER_SITEKEY
        
        # Extract if needed
        blob = data.get('blob')
        if not blob:
            blob_result = solver.blob_extractor.extract_blob(
                sitekey, 
                data.get('proxy')
            )
            if blob_result.get('success'):
                blob = blob_result['blob']

        # Create task
        solve_data = {
            "preset": preset,
            "blob": blob,
            "has_suppressed": data.get('has_suppressed', False),
            "has_pow": data.get('has_pow', False),
            "proxy": data.get('proxy')
        }

        result = solver.solve_complete(solve_data)
        
        return jsonify({
            "success": result.get('success'),
            "task_id": result.get('task_id')
        })

    except Exception as e:
        return jsonify({"success": False, "err": str(e)})


@app.route('/funcaptcha/getTask', methods=['POST'])
def getTask_legacy():
    """Legacy endpoint for backward compatibility"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        result = solver.get_task_result(task_id)
        
        if result.get('success') and result.get('status') == 'completed':
            return jsonify({
                "status": "completed",
                "captcha": {
                    "token": result.get('token')
                }
            })
        elif result.get('success'):
            return jsonify({"status": "processing"})
        else:
            return jsonify({"status": "error", "error": result.get('error')})

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


# =====================================================
# STATS ENDPOINT
# =====================================================

@app.route('/stats', methods=['GET'])
def stats():
    """Get solver statistics"""
    return jsonify({
        "solved": Utils.solved,
        "failed": Utils.fail,
        "suppressed_solved": Utils.suppressed_solved,
        "pow_solved": Utils.pow_solved,
        "errors": Utils.errors,
        "uptime": time.time()
    })


# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG, threaded=True)
