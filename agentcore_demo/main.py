"""Cloud entrypoint; no dotenv loading or embedded credentials."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentcore_demo.runtime import app
app.run()

