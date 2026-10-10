"""Build an allowlisted Linux ARM64 deployment ZIP; never traverse the repo."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["rag_smoke_test.py", "rag/app.py", "rag/nl2sql.py",
           "agentcore_demo/__init__.py", "agentcore_demo/runtime.py",
           "agentcore_demo/main.py"]

def main():
    output = ROOT / ".runtime" / "agentcore.zip"
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="agentcore-build-") as directory:
        stage = Path(directory)
        subprocess.run([sys.executable, "-m", "pip", "install",
            "--platform", "manylinux2014_aarch64", "--python-version", "3.13",
            "--implementation", "cp", "--abi", "cp313", "--only-binary=:all:",
            "--no-compile", "--target", str(stage),
            "-r", str(ROOT / "agentcore_demo/requirements.txt")], check=True)
        for name in SOURCES:
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    info = zipfile.ZipInfo(path.relative_to(stage).as_posix())
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes())
    print(output)

if __name__ == "__main__":
    main()

