import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_app_imports():
    app_path = ROOT / "app.py"
    assert app_path.exists()

    spec = importlib.util.spec_from_file_location("app_module", app_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    assert hasattr(module, "st")
