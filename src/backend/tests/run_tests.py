#!/usr/bin/env python3
"""
测试入口脚本 - 一键运行全量测试

用法：
    python tests/run_tests.py             # 运行所有测试
    python tests/run_tests.py --unit       # 只运行单元测试
    python tests/run_tests.py --integration # 只运行集成测试
    python tests/run_tests.py --api       # 只运行API测试
    python tests/run_tests.py --cov      # 运行测试并生成覆盖率报告
    python tests/run_tests.py --fast     # 快速运行（跳过慢速测试）
    python tests/run_tests.py --md       # 生成Markdown测试报告（默认：tests/report.md）
    python tests/run_tests.py --md report.md  # 指定报告文件路径
"""
import sys
import subprocess
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="运行物流系统后端测试")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--api", action="store_true", help="只运行API测试")
    parser.add_argument("--cov", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--fast", action="store_true", help="快速运行（跳过慢速测试）")
    parser.add_argument("--md", type=str, nargs="?", const="tests/report.md", help="生成Markdown测试报告（可指定路径，默认：tests/report.md）")
    parser.add_argument("--phase", type=str, help="运行特定阶段的测试（如：--phase phase1）")
    args = parser.parse_args()
    
    # 构建pytest命令
    cmd = [sys.executable, "-m", "pytest"]
    
    # 添加标记过滤
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.api:
        cmd.extend(["-m", "api"])
    elif args.phase:
        cmd.extend(["-m", args.phase])
    
    # 快速运行：跳过慢速测试
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    # 覆盖率报告
    if args.cov:
        cmd.extend(["--cov=.", "--cov-report=html:htmlcov", "--cov-report=term"])
    
    # Markdown报告
    if args.md:
        # 确保报告文件的目录存在
        report_dir = os.path.dirname(args.md)
        if report_dir and not os.path.exists(report_dir):
            os.makedirs(report_dir, exist_ok=True)
        cmd.extend(["--md", args.md])
    
    # 添加详细输出
    if not args.fast:
        cmd.append("-v")
    
    # 添加测试路径
    cmd.append("tests/")
    
    # 执行测试
    print(f"执行命令：{' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
