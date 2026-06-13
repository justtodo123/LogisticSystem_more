#!/usr/bin/env python
"""运行 test_route_planning.py::TestRunRoutePlanning::test_valid_dispatch_id 测试并查看详细输出"""
import subprocess
import sys

def main():
    """主函数"""
    # 运行测试
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "tests/test_route_planning.py::TestRunRoutePlanning::test_valid_dispatch_id", 
         "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="d:\\Git Demo\\LogisticSystem\\src\\backend"
    )
    
    # 打印输出
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print("\nReturn code:", result.returncode)

if __name__ == "__main__":
    main()
