#!/usr/bin/env python3
"""
运行阶段4所有测试
"""
import subprocess
import sys

def run_tests():
    """运行阶段4测试"""
    tests = [
        ("算法层测试", "tests/test_algorithms/test_node_dispatch.py"),
        ("服务层测试", "tests/test_services/test_dispatch_service.py"),
        ("API层测试", "tests/test_api/test_node_dispatch_api.py"),
    ]
    
    results = []
    
    for name, path in tests:
        print(f"\n{'='*60}")
        print(f"运行{name}：{path}")
        print('='*60)
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", path, "-v", "--tb=short"],
            cwd="d:\\Git Demo\\LogisticSystem\\src\\backend"
        )
        
        results.append((name, result.returncode))
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print('='*60)
    
    all_passed = True
    for name, code in results:
        status = "[PASS] 通过" if code == 0 else "[FAIL] 失败"
        print(f"{name}：{status}")
        if code != 0:
            all_passed = False
    
    if all_passed:
        print("\n[PASS] 所有测试通过！")
        return 0
    else:
        print("\n[FAIL] 部分测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
