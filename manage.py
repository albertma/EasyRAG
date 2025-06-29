#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EasyRAG.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # 初始化 RAG 组件（在 Django 设置加载后）
    try:
        from EasyRAG.common import init_rag_components
        init_rag_components()
    except Exception as e:
        print(f"Warning: Failed to initialize RAG components: {e}")
    
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
