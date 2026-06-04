"""FamilyHub - 家庭信息共享应用入口"""
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "417"))
    print(f"*** FamilyHub Starting ***")
    print(f"URL: http://{host}:{port}")
    if debug:
        print("[WARNING] Debug mode is ON. Do NOT use in production!")
    app.run(host=host, port=port, debug=debug)
