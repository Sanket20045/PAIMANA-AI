import uvicorn
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.db import init_db
from backend.data_service import seed_demo_data, get_all_analyzed_projects

def main():
    print("=" * 70)
    print("PAIMANA AI - Infrastructure Project Early Warning & Decision Support System")
    print("Official Prototype Platform | SIH 2026")
    print("Predict -> Explain -> Prioritize -> Recommend")
    print("=" * 70)
    
    # Initialize DB and seed initial projects
    init_db()
    projects = get_all_analyzed_projects()
    print(f"[*] SQLite Database initialized with {len(projects)} infrastructure projects.")
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    print(f"[*] Launching Uvicorn server at http://{host}:{port} ...")
    print("=" * 70)
    
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
