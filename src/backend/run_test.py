"""临时测试脚本"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/api/test_exceptions.py", "-v", "--tb=short", "--cache-clear"],
    capture_output=True,
    text=True,
    cwd=r"D:\Git Demo\LogisticSystem\src\backend"
)
print("STDOUT:")
print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
print("\nSTDERR:")
print(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)
print(f"\nEXIT CODE: {result.returncode}")
