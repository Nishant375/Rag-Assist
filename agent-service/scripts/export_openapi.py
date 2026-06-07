"""
Export the FastAPI OpenAPI spec straight from the app — no running server needed.

Usage:
    python scripts/export_openapi.py [output_path]

Defaults to writing ../frontend/openapi.json so the frontend codegen input
always reflects the current backend code.
"""

import json
import sys
from pathlib import Path

# Make the agent-service package root importable regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import app  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../frontend/openapi.json")
out.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
print(f"Wrote OpenAPI spec → {out}")
