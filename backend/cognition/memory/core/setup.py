#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
持久化记忆系统 - 快速设置脚本
"""
import os
import sys
import subprocess
import time


def print_header(text):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_docker():
    """检查Docker是否运行"""
    try:
        result = subprocess.run(
            ["docker", "ps"], capture_output=True, text=True, check=True
        )
        return True
    except:
        return False


def check_env_file():
    """检查环境变量文件"""
    env_path = os.path.join(os.path.dirname(__file__), "..", "slide_agent", ".env")
    return os.path.exists(env_path)


def setup_services():
    """启动数据库服务"""
    print_header("1. 启动PostgreSQL和Redis服务")

    if not check_docker():
        print("❌ Docker未运行，请先启动Docker Desktop")
        return False

    backend_dir = os.path.join(os.path.dirname(__file__), "..")

    try:
        print("正在启动服务...")
        subprocess.run(
            ["docker-compose", "up", "-d", "postgres", "redis"],
            cwd=backend_dir,
            check=True,
        )

        print("\n⏳ 等待服务启动（20秒）...")
        time.sleep(20)

        print("✅ 服务已启动")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动服务失败: {e}")
        return False


def init_database():
    """初始化数据库"""
    print_header("2. 初始化数据库表和索引")

    try:
        from database import get_db

        print("正在创建表...")
        db = get_db()
        db.init_db(drop_existing=False)

        print("✅ 数据库初始化成功")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


def health_check():
    """健康检查"""
    print_header("3. 系统健康检查")

    try:
        from database import get_db
        from redis_cache import RedisCache
        from vector_memory_service import VectorMemoryService

        # 检查PostgreSQL
        db = get_db()
        if db.health_check():
            print("✅ PostgreSQL: 正常")
        else:
            print("❌ PostgreSQL: 连接失败")
            return False

        # 检查Redis
        cache = RedisCache()
        if cache.is_available():
            print("✅ Redis: 正常")
        else:
            print("⚠️  Redis: 不可用（将降级到无缓存模式）")

        # 检查向量服务
        vector_service = VectorMemoryService()
        if vector_service.is_available():
            print("✅ 向量服务: 正常")
        else:
            print("⚠️  向量服务: 不可用（需要配置OPENAI_API_KEY）")

        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def show_next_steps():
    """显示后续步骤"""
    print_header("🎉 设置完成！")

    print("后续步骤：")
    print("\n1. 配置环境变量:")
    print("   - 复制 backend/env_template_memory 到 backend/slide_agent/.env")
    print("   - 填入你的 OPENAI_API_KEY（用于向量embeddings）")
    print("   - 设置 USE_PERSISTENT_MEMORY=true")

    print("\n2. 启动Agent服务:")
    print("   cd backend")
    print("   docker-compose up -d ppt_agent ppt_outline")

    print("\n3. 查看文档:")
    print("   查看 backend/persistent_memory/README.md")

    print("\n4. 监控服务:")
    print("   docker-compose logs -f postgres redis")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    print(
        """
    ╔═══════════════════════════════════════════════════════╗
    ║  MultiAgentPPT - 持久化记忆系统 设置向导               ║
    ║  PostgreSQL + Redis + pgvector                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    )

    # 检查环境变量
    if not check_env_file():
        print("⚠️  未找到 .env 文件")
        print("   请先复制 backend/env_template_memory 到 backend/slide_agent/.env")
        print("   并填入必要的配置（OPENAI_API_KEY等）\n")
        response = input("是否继续？(y/n): ")
        if response.lower() != "y":
            sys.exit(0)

    # 步骤1: 启动服务
    if not setup_services():
        print("\n❌ 设置失败，请检查错误信息")
        sys.exit(1)

    # 步骤2: 初始化数据库
    if not init_database():
        print("\n❌ 设置失败，请检查错误信息")
        sys.exit(1)

    # 步骤3: 健康检查
    if not health_check():
        print("\n⚠️  部分服务不可用，但基础功能可以运行")

    # 显示后续步骤
    show_next_steps()


if __name__ == "__main__":
    main()
