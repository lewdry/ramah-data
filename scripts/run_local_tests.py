"""Simple harness to run the repository's pytest-style tests without pytest installed.

This script imports test modules and runs their test functions directly by providing a
`tmp_path` value created via `tempfile.TemporaryDirectory()` as a pathlib.Path.

Use this for quick local validation when pytest isn't available.
"""
import importlib.util
import tempfile
import pathlib
import sys

def run_test_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Run all callables named test_* with a tmp_path argument
    for name in dir(module):
        if name.startswith('test_') and callable(getattr(module, name)):
            func = getattr(module, name)
            print(f"Running {module.__name__}.{name}()")
            with tempfile.TemporaryDirectory() as td:
                tmp_path = pathlib.Path(td)
                # If the test expects a tmp_path argument, pass it; otherwise call with no args
                try:
                    func(tmp_path)
                except TypeError:
                    func()

if __name__ == '__main__':
    tests = [pathlib.Path(__file__).parent.parent / 'tests' / 'test_data_format.py']
    failed = False
    for t in tests:
        try:
            run_test_module(t)
        except Exception as e:
            print(f"Test module {t} failed: {e}")
            failed = True
    if failed:
        sys.exit(1)
    print("All local tests passed.")
