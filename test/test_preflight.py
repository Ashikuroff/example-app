from pathlib import Path
import importlib.util


def load_preflight(path):
    spec = importlib.util.spec_from_file_location("preflight", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_detection_functions():
    root = Path(".")
    mod = load_preflight(".github/skills/azure-deployment-preflight/preflight.py")
    # azd detection returns a bool
    assert isinstance(mod.find_azd_project(root), bool)
    # detection of bicep files should return a list
    files = mod.find_bicep_files(root)
    assert isinstance(files, list)
    # target scope for a non-existent file should be None or default
    p = Path("nonexistent.bicep")
    assert mod.get_target_scope(p) in (None, "resourceGroup")
