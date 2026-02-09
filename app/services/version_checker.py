"""
版本检查服务
检测 NovelVoice 和 edge-tts 等核心依赖的版本更新
"""

import asyncio
import aiohttp
from typing import Optional, Dict
from packaging import version
import importlib.metadata
import logging
from app.core.config import VERSION

logger = logging.getLogger(__name__)


class VersionChecker:
    """
    版本检查器
    
    功能:
    - 获取已安装的包版本
    - 从 PyPI 获取 edge-tts 最新版本
    - 从 GitHub 获取 NovelVoice 最新版本
    - 比较版本并记录更新信息
    """
    
    def __init__(self):
        self.update_info: Optional[Dict] = None
        self.app_update_info: Optional[Dict] = None
        self.latest_app_version: Optional[str] = None
        self.checking = False
    
    def get_installed_version(self, package: str) -> Optional[str]:
        """
        获取已安装的包版本
        """
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None
        except Exception as e:
            logger.warning(f"⚠️  获取 {package} 版本失败: {e}")
            return None

    def get_app_version(self) -> str:
        """获取当前应用版本"""
        return VERSION
    
    async def get_latest_pypi_version(self, package: str) -> Optional[str]:
        """从 PyPI 获取最新版本"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://pypi.org/pypi/{package}/json"
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['info']['version']
                    return None
        except Exception as e:
            logger.warning(f"⚠️  获取 {package} PyPI 版本失败: {e}")
            return None

    async def get_latest_github_version(self, repo: str) -> Optional[str]:
        """从 GitHub 获取最新 Release 版本"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.github.com/repos/{repo}/releases/latest"
                headers = {"Accept": "application/vnd.github.v3+json"}
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get(url, headers=headers, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tag = data['tag_name']
                        # 移除 'v' 前缀
                        if tag.startswith('v'):
                            tag = tag[1:]
                        return tag
                    return None
        except Exception as e:
            logger.warning(f"⚠️  获取 {repo} GitHub 版本失败: {e}")
            return None
    
    async def check_update(self, package: str = "edge-tts", repo: str = "skyshenma/NovelVoice"):
        """检查更新"""
        if self.checking:
            return
        
        self.checking = True
        try:
            # 1. 检查 edge-tts (Engine)
            current_engine = self.get_installed_version(package)
            if current_engine:
                latest_engine = await self.get_latest_pypi_version(package)
                if latest_engine and version.parse(latest_engine) > version.parse(current_engine):
                    self.update_info = {
                        "type": "engine",
                        "package": package,
                        "current_version": current_engine,
                        "latest_version": latest_engine,
                        "has_update": True
                    }
                else:
                    self.update_info = None

            # 2. 检查 NovelVoice (App)
            current_app = self.get_app_version()
            latest_app = await self.get_latest_github_version(repo)
            self.latest_app_version = latest_app
            
            if latest_app and version.parse(latest_app) > version.parse(current_app):
                self.app_update_info = {
                    "type": "app",
                    "repo": repo,
                    "current_version": current_app,
                    "latest_version": latest_app,
                    "has_update": True
                }
            else:
                self.app_update_info = None

        except Exception as e:
            logger.error(f"❌ 版本检查过程中出错: {e}")
        finally:
            self.checking = False
    
    def get_status(self) -> Dict:
        """获取综合版本状态"""
        return {
            "app_version": self.get_app_version(),
            "latest_app_version": self.latest_app_version or self.get_app_version(),
            "app_update_available": self.app_update_info is not None,
            "engine_version": self.get_installed_version("edge-tts"),
            "engine_update_available": self.update_info is not None,
            "update_info": self.app_update_info or self.update_info # 优先提示 App 更新
        }

    def clear_update_info(self):
        """清除更新信息"""
        self.update_info = None
        self.app_update_info = None


# 全局实例
version_checker = VersionChecker()
