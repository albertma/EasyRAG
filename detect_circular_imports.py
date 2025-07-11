#!/usr/bin/env python3
"""
循环导入检测工具
使用方法: python detect_circular_imports.py
"""

import sys
import os
import importlib.util
from collections import defaultdict, deque
from typing import Set, Dict, List, Tuple

class CircularImportDetector:
    def __init__(self):
        self.import_graph = defaultdict(set)
        self.visited = set()
        self.recursion_stack = set()
        self.circular_imports = []
        
    def add_import(self, from_module: str, to_module: str):
        """添加导入关系"""
        self.import_graph[from_module].add(to_module)
    
    def detect_circular_imports(self) -> List[List[str]]:
        """检测循环导入"""
        self.circular_imports = []
        self.visited = set()
        
        for module in self.import_graph:
            if module not in self.visited:
                self._dfs(module, [])
        
        return self.circular_imports
    
    def _dfs(self, module: str, path: List[str]):
        """深度优先搜索检测循环"""
        if module in self.recursion_stack:
            # 发现循环导入
            cycle_start = path.index(module)
            cycle = path[cycle_start:] + [module]
            self.circular_imports.append(cycle)
            return
        
        if module in self.visited:
            return
        
        self.visited.add(module)
        self.recursion_stack.add(module)
        path.append(module)
        
        for next_module in self.import_graph[module]:
            self._dfs(next_module, path)
        
        path.pop()
        self.recursion_stack.remove(module)
    
    def analyze_python_file(self, file_path: str, base_path: str = "") -> Set[Tuple[str, str]]:
        """分析Python文件中的导入语句"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            current_module = self._get_module_name(file_path, base_path)
            
            for line in lines:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 检测 from ... import 语句
                if line.startswith('from '):
                    parts = line.split(' import ')
                    if len(parts) == 2:
                        from_part = parts[0][5:]  # 去掉 'from '
                        imported_modules = parts[1].split(', ')
                        
                        for imported in imported_modules:
                            imported = imported.strip()
                            if imported and not imported.startswith('#'):
                                # 处理相对导入
                                if from_part.startswith('.'):
                                    # 相对导入，需要计算绝对路径
                                    relative_level = len(from_part) - len(from_part.lstrip('.'))
                                    from_module = self._resolve_relative_import(
                                        current_module, from_part, relative_level
                                    )
                                else:
                                    from_module = from_part
                                
                                imports.add((current_module, from_module))
                
                # 检测 import 语句
                elif line.startswith('import '):
                    import_part = line[7:]  # 去掉 'import '
                    imported_modules = import_part.split(', ')
                    
                    for imported in imported_modules:
                        imported = imported.strip()
                        if imported and not imported.startswith('#'):
                            imports.add((current_module, imported))
        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return imports
    
    def _get_module_name(self, file_path: str, base_path: str) -> str:
        """获取模块名"""
        if base_path:
            rel_path = os.path.relpath(file_path, base_path)
        else:
            rel_path = file_path
        
        # 移除 .py 扩展名
        if rel_path.endswith('.py'):
            rel_path = rel_path[:-3]
        
        # 将路径分隔符替换为点
        module_name = rel_path.replace(os.sep, '.')
        
        return module_name
    
    def _resolve_relative_import(self, current_module: str, relative_path: str, level: int) -> str:
        """解析相对导入"""
        if level == 0:
            return relative_path
        
        # 计算父模块路径
        parts = current_module.split('.')
        if level > len(parts):
            return relative_path  # 无法解析
        
        parent_module = '.'.join(parts[:-level])
        if relative_path.startswith('.'):
            relative_path = relative_path[level:]
        
        if relative_path:
            return f"{parent_module}.{relative_path}"
        else:
            return parent_module
    
    def scan_directory(self, directory: str) -> Dict[str, Set[Tuple[str, str]]]:
        """扫描目录中的所有Python文件"""
        all_imports = {}
        
        for root, dirs, files in os.walk(directory):
            # 跳过 __pycache__ 和 .git 目录
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'env', 'venv']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    imports = self.analyze_python_file(file_path, directory)
                    if imports:
                        all_imports[file_path] = imports
        
        return all_imports

def main():
    """主函数"""
    detector = CircularImportDetector()
    
    # 扫描当前目录
    current_dir = os.getcwd()
    print(f"扫描目录: {current_dir}")
    
    all_imports = detector.scan_directory(current_dir)
    
    # 构建导入图
    for file_path, imports in all_imports.items():
        for from_module, to_module in imports:
            detector.add_import(from_module, to_module)
    
    # 检测循环导入
    circular_imports = detector.detect_circular_imports()
    
    if circular_imports:
        print("\n🚨 发现循环导入:")
        for i, cycle in enumerate(circular_imports, 1):
            print(f"\n循环 {i}:")
            for j, module in enumerate(cycle[:-1]):
                print(f"  {module} -> {cycle[j+1]}")
    else:
        print("\n✅ 未发现循环导入")
    
    # 显示所有导入关系
    print(f"\n📊 导入关系统计:")
    print(f"总文件数: {len(all_imports)}")
    print(f"总导入关系数: {sum(len(imports) for imports in all_imports.values())}")
    
    # 显示每个文件的导入
    print(f"\n📁 各文件导入详情:")
    for file_path, imports in all_imports.items():
        if imports:
            print(f"\n{file_path}:")
            for from_module, to_module in imports:
                print(f"  {from_module} -> {to_module}")

if __name__ == "__main__":
    main() 