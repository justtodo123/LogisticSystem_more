"""临时测试脚本 - 详细输出"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/api/test_exceptions.py::TestExceptionAPI::test_create_exception_resets_status",
     "-v", "--tb=long", "--cache-clear", "-s"],
    capture_output=True,
    text=True,
    cwd=r"D:\Git Demo\LogisticSystem\src\backend"
)
print("STDOUT (last 3000 chars):")
print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
print("\nSTDERR (last 1000 chars):")
print(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)
print(f"\nEXIT CODE: {result.returncode}")
