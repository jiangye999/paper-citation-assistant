# 上传完整代码到 GitHub 的脚本

import os
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(r"E:\AI_projects\论文反插助手 - 副本")

print("=" * 60)
print("论文反插助手 - 上传完整代码到 GitHub")
print("=" * 60)

# 检查 Git
print("\n[1/4] 检查 Git 状态...")
try:
    result = subprocess.run(["git", "--version"], capture_output=True, text=True)
    print(f"✓ Git 已安装：{result.stdout.strip()}")
except:
    print("✗ Git 未安装，请先安装 Git：https://git-scm.com/")
    input("按回车退出...")
    exit(1)

# 检查是否在 Git 仓库中
os.chdir(PROJECT_ROOT)
try:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True
    )
    if result.returncode != 0:
        print("✗ 当前目录不是 Git 仓库")
        print("\n请先运行以下命令初始化 Git：")
        print("  git init")
        input("按回车退出...")
        exit(1)
    print("✓ 在 Git 仓库中")
except:
    print("✗ Git 检查失败")
    input("按回车退出...")
    exit(1)

# 配置 Git 用户
print("\n[2/4] 配置 Git 用户信息...")
name = input("请输入你的 GitHub 用户名（默认：jiangye999）: ").strip()
if not name:
    name = "jiangye999"
email = input("请输入你的邮箱（默认：不设置）: ").strip()

subprocess.run(["git", "config", "user.name", name])
if email:
    subprocess.run(["git", "config", "user.email", email])
print(f"✓ Git 用户设置为：{name}")

# 添加所有文件
print("\n[3/4] 添加文件...")
print("  正在添加所有文件到 Git...")

# 先添加 .gitattributes（如果有 LFS）
gitattributes = PROJECT_ROOT / ".gitattributes"
if gitattributes.exists():
    subprocess.run(["git", "add", ".gitattributes"])
    print("  ✓ 添加 .gitattributes")

# 添加其他文件
subprocess.run(["git", "add", "."])
print("  ✓ 添加所有文件")

# 查看状态
result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
if result.stdout.strip():
    print(f"\n即将提交的文件:")
    print(result.stdout[:500])
    if len(result.stdout) > 500:
        print(f"... 还有 {len(result.stdout.splitlines()) - 20} 个文件")
else:
    print("  没有需要提交的文件（已经是最新）")

# 提交
print("\n[4/4] 提交更改...")
commit_msg = "Upload complete project files including src modules and build scripts"
subprocess.run(["git", "commit", "-m", commit_msg])
print("✓ 提交完成")

# 检查远程仓库
print("\n检查远程仓库...")
result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
if "origin" not in result.stdout:
    print("✗ 未找到远程仓库 'origin'")
    print("\n请运行以下命令添加远程仓库：")
    print(
        f"  git remote add origin https://github.com/{name}/paper-citation-assistant.git"
    )
    response = input("\n是否现在添加？(y/n): ").strip().lower()
    if response == "y":
        repo_url = f"https://github.com/{name}/paper-citation-assistant.git"
        subprocess.run(["git", "remote", "add", "origin", repo_url])
        print(f"✓ 已添加远程仓库：{repo_url}")
    else:
        print("⚠ 请手动添加远程仓库后再推送")
        input("按回车退出...")
        exit(1)

# 推送到 GitHub
print("\n推送到 GitHub...")
print("⚠️  注意：如果文件较大（特别是 models/），可能需要几分钟")
print("⚠️  如果推送失败，请安装 Git LFS：git lfs install")

response = input("是否现在推送？(y/n): ").strip().lower()
if response == "y":
    print("\n正在推送到 GitHub...")
    result = subprocess.run(
        ["git", "push", "-u", "origin", "main"], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("\n✅ 推送成功！")
        print(f"\n访问你的仓库：https://github.com/{name}/paper-citation-assistant")
        print("\n下一步：")
        print("1. 访问上述 GitHub 仓库页面")
        print("2. 点击 'Actions' 标签")
        print("3. 点击 'Build and Release Windows EXE'")
        print("4. 点击 'Run workflow' 开始打包")
    else:
        print("\n❌ 推送失败！")
        print("\n错误信息：")
        print(result.stderr[-500:])

        if (
            "large file" in result.stderr.lower()
            or "rejecting" in result.stderr.lower()
        ):
            print("\n⚠️  检测到有大文件被拒绝")
            print("请安装 Git LFS：")
            print("  git lfs install")
            print('  git lfs track "models/*"')
            print("  git add .gitattributes models/")
            print("  git commit -m 'Add models with LFS'")
            print("  git push origin main")
        else:
            print("\n可能的原因：")
            print("1. 网络连接问题")
            print("2. 没有 GitHub 访问权限")
            print("3. 仓库不存在")
            print("\n请检查后重试")
else:
    print("\n⚠️  已取消推送")
    print("\n你可以稍后手动运行：git push -u origin main")

print("\n" + "=" * 60)
print("完成！")
print("=" * 60)
input("按回车退出...")
