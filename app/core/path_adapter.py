"""
路径自适应系统
自动检测和适配数据存储路径,提升跨平台兼容性
"""

import os
import pathlib
import shutil
from typing import List, Optional, Tuple
from enum import Enum


class PathType(Enum):
    """路径类型枚举"""
    DATA = "data_dir"
    APP_DATA = "app_data_dir"
    CACHE = "cache_dir"


class PathAdapter:
    """
    路径适配器
    
    功能:
    - 智能检测可用路径
    - 按优先级尝试候选路径
    - 自动验证权限
    - 检测和迁移旧数据
    """
    
    def __init__(self, project_root: pathlib.Path):
        """
        初始化路径适配器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.user_home = pathlib.Path.home()
        
    def get_candidates(
        self, 
        path_type: PathType, 
        config_path: Optional[str] = None
    ) -> List[pathlib.Path]:
        """
        获取候选路径列表(按优先级排序)
        
        Args:
            path_type: 路径类型
            config_path: 配置文件中指定的路径(最高优先级)
            
        Returns:
            候选路径列表
        """
        candidates = []
        
        # 1. 配置文件指定的路径(最高优先级)
        if config_path:
            path = self._resolve_path(config_path)
            candidates.append(path)
        
        # 2. 根据路径类型添加候选路径
        if path_type == PathType.DATA:
            candidates.extend([
                self.project_root / "data",
                self.user_home / ".novelvoice" / "data",
                pathlib.Path("/tmp/novelvoice/data"),
            ])
        elif path_type == PathType.APP_DATA:
            candidates.extend([
                self.project_root / "data" / "app",
                self.user_home / ".novelvoice" / "data" / "app",
                pathlib.Path("/tmp/novelvoice/data/app"),
            ])
        elif path_type == PathType.CACHE:
            candidates.extend([
                self.project_root / "data" / "cache",
                self.user_home / ".cache" / "novelvoice",
                pathlib.Path("/tmp/novelvoice/cache"),
            ])
        
        return candidates
    
    def find_writable_path(
        self, 
        candidates: List[pathlib.Path],
        create: bool = True
    ) -> Optional[pathlib.Path]:
        """
        找到第一个可写的路径
        
        Args:
            candidates: 候选路径列表
            create: 是否自动创建目录
            
        Returns:
            可写的路径,如果都不可写则返回 None
        """
        for path in candidates:
            if self._is_writable(path, create):
                return path
        return None
    
    def _is_writable(self, path: pathlib.Path, create: bool = True) -> bool:
        """
        检查路径是否可写
        
        Args:
            path: 要检查的路径
            create: 是否尝试创建目录
            
        Returns:
            是否可写
        """
        try:
            # 尝试创建目录
            if create:
                path.mkdir(parents=True, exist_ok=True)
            elif not path.exists():
                return False
            
            # 测试写入权限
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False
    
    def detect_old_data(
        self, 
        new_path: pathlib.Path, 
        candidates: List[pathlib.Path]
    ) -> Optional[pathlib.Path]:
        """
        检测是否有旧数据需要迁移
        
        Args:
            new_path: 新路径
            candidates: 候选路径列表
            
        Returns:
            包含数据的旧路径,如果没有则返回 None
        """
        for old_path in candidates:
            if old_path == new_path:
                continue
            if old_path.exists() and self._has_data(old_path):
                return old_path
        return None
    
    def _has_data(self, path: pathlib.Path) -> bool:
        """
        检查路径是否包含数据
        
        Args:
            path: 要检查的路径
            
        Returns:
            是否包含数据
        """
        if not path.exists():
            return False
        
        try:
            # 检查是否有文件或非空子目录
            for item in path.iterdir():
                # 忽略隐藏文件和测试文件
                if item.name.startswith('.'):
                    continue
                return True
            return False
        except (PermissionError, OSError):
            return False
    
    def migrate_data(
        self, 
        old_path: pathlib.Path, 
        new_path: pathlib.Path,
        move: bool = False
    ) -> bool:
        """
        迁移数据
        
        Args:
            old_path: 旧路径
            new_path: 新路径
            move: 是否移动(True)还是复制(False)
            
        Returns:
            是否成功
        """
        try:
            print(f"\n📦 {'移动' if move else '复制'}数据:")
            print(f"   源: {old_path}")
            print(f"   目标: {new_path}")
            
            # 确保目标目录存在
            new_path.mkdir(parents=True, exist_ok=True)
            
            # 统计文件数量
            file_count = 0
            
            # 迁移所有文件和目录
            for item in old_path.iterdir():
                # 忽略隐藏文件和测试文件
                if item.name.startswith('.'):
                    continue
                
                src = old_path / item.name
                dst = new_path / item.name
                
                if src.is_dir():
                    if move:
                        shutil.move(str(src), str(dst))
                    else:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    file_count += sum(1 for _ in dst.rglob('*') if _.is_file())
                else:
                    if move:
                        shutil.move(str(src), str(dst))
                    else:
                        shutil.copy2(src, dst)
                    file_count += 1
            
            print(f"✅ 数据迁移完成 (共 {file_count} 个文件)")
            return True
        except Exception as e:
            print(f"❌ 数据迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _resolve_path(self, path_str: str) -> pathlib.Path:
        """
        解析路径字符串,支持相对路径和绝对路径
        
        Args:
            path_str: 路径字符串
            
        Returns:
            解析后的 Path 对象
        """
        path = pathlib.Path(path_str)
        if path.is_absolute():
            return path
        else:
            return self.project_root / path
    
    def get_relative_path(self, absolute_path: pathlib.Path) -> Optional[str]:
        """
        获取相对于项目根目录的相对路径
        
        Args:
            absolute_path: 绝对路径
            
        Returns:
            相对路径字符串,如果不在项目内则返回 None
        """
        try:
            rel_path = absolute_path.relative_to(self.project_root)
            return str(rel_path)
        except ValueError:
            # 不在项目内
            return None


def get_env_path(env_var: str) -> Optional[pathlib.Path]:
    """
    从环境变量获取路径
    
    Args:
        env_var: 环境变量名
        
    Returns:
        路径对象,如果环境变量不存在则返回 None
    """
    path_str = os.getenv(env_var)
    if path_str:
        return pathlib.Path(path_str)
    return None
