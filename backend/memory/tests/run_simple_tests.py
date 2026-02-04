"""
运行 Memory 层单元测试
"""
import subprocess
import sys

# 设置工作目录
import os
os.chdir(r"C:\Users\yanzikun\Desktop\CS\5. Project\MultiAgentPPT-main\backend\memory\tests")

print("运行 Memory 层单元测试...")
print("=" * 60)

# 运行数据模型测试（最简单的）
print("\n[1/3] 运行数据模型测试...")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "unit/test_models.py::TestMemoryMetadata", "-v", "--tb=short"],
    capture_output=True,
    text=True
)

# 显示输出（限制行数）
lines = result.stdout.split('\n')[:50]
for line in lines:
    if line.strip():
        print(line)

if result.returncode == 0:
    print("\n[SUCCESS] 数据模型测试通过！")
else:
    print(f"\n[FAILED] 测试失败，退出码: {result.returncode}")
    # 显示错误输出
    if result.stderr:
        print("\n错误输出:")
        print(result.stderr[:500])

print("\n测试完成！")
