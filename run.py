"""
One-click launcher for RIOS - python run.py
"""
import os, sys, subprocess, time
from pathlib import Path
ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

api_key = os.getenv("GROQ_API_KEY", "")
if not api_key:
    print("Get free key at https://console.groq.com")
    api_key = input("Enter GROQ_API_KEY (gsk_...) or Enter for mock mode: ").strip()

env_content = f"GROQ_API_KEY={api_key}\nGROQ_MODEL=openai/gpt-oss-120b\nGROQ_BASE_URL=https://api.groq.com/openai/v1\n" if api_key else "GROQ_MODEL=openai/gpt-oss-120b\n"
print("=== RIOS Setup ===")
(BACKEND / ".env").write_text(env_content)
print("[1/4] .env created")
print("[2/4] Installing backend deps...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(BACKEND / "requirements.txt")], check=False)
print("[3/4] Checking frontend...")
if not (FRONTEND / "node_modules").exists():
    subprocess.run(["npm", "install"], cwd=str(FRONTEND), shell=True, check=False)
print("[4/4] Starting servers on 8000 and 3000...")
backend_proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"], cwd=str(BACKEND))
time.sleep(3)
print("Open http://localhost:3000")
try:
    subprocess.run(["npm", "run", "dev"], cwd=str(FRONTEND), shell=True)
except KeyboardInterrupt:
    backend_proc.terminate()
