"""
版本检查服务
检测 edge-tts 等核心依赖的版本更新
"""

import asyncio
import aiohttp
from typing import Optional, Dict
from packaging import version
import importlib.metadata


class VersionChecker:
    """
    版本检查器
    
    功能:
    - 获取已安装的包版本
    - 从 PyPI 获取最新版本
    - 比较版本并记录更新信息
    """
    
    def __init__(self):
        self.update_info: Optional[Dict] = None
        self.checking = False
    
    def get_installed_version(self, package: str) -> Optional[str]:
        """
        获取已安装的包版本
        
        Args:
            package: 包名
            
        Returns:
            版本号字符串,如果包未安装则返回 None
        """
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None
        except Exception as e:
            print(f"⚠️  获取 {package} 版本失败: {e}")
            return None
    
    async def get_latest_version(self, package: str) -> Optional[str]:
        """
        从 PyPI 获取最新版本
        
        Args:
            package: 包名
            
        Returns:
            最新版本号字符串,如果获取失败则返回 None
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://pypi.org/pypi/{package}/json"
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['info']['version']
                    else:
                        print(f"⚠️  PyPI 返回状态码: {resp.status}")
                        return None
        except asyncio.TimeoutError:
            print(f"⚠️  获取 {package} 最新版本超时")
            return None
        except Exception as e:
            print(f"⚠️  获取 {package} 最新版本失败: {e}")
            return None
    
    async def check_update(self, package: str = "edge-tts") -> Optional[Dict]:
        """
        检查更新
        
        Args:
            package: 要检查的包名
            
        Returns:
            更新信息字典,如果没有更新则返回 None
        """
        if self.checking:
            print(f"⏳ 正在检查 {package} 版本...")
            return None
        
        self.checking = True
        try:
            print(f"\n🔍 检查 {package} 版本更新...")
            
            # 获取当前版本
            current = self.get_installed_version(package)
            if not current:
                print(f"❌ 未找到 {package} 包")
                return None
            
            print(f"   当前版本: {current}")
            
            # 获取最新版本
            latest = await self.get_latest_version(package)
            if not latest:
                print(f"⚠️  无法获取 {package} 最新版本")
                return None
            
            print(f"   最新版本: {latest}")
            
            # 比较版本
            if version.parse(latest) > version.parse(current):
                print(f"📦 发现新版本: {current} → {latest}")
                self.update_info = {
                    "package": package,
                    "current_version": current,
                    "latest_version": latest,
                    "has_update": True
                }
                return self.update_info
            else:
                print(f"✅ {package} 已是最新版本")
                return None
        except Exception as e:
            print(f"❌ 版本检查失败: {e}")
            return None
        finally:
            self.checking = False
    
    def get_update_info(self) -> Optional[Dict]:
        """
        获取更新信息
        
        Returns:
            更新信息字典,如果没有更新则返回 None
        """
        return self.update_info
    
    def clear_update_info(self):
        """清除更新信息(用户忽略更新时调用)"""
        self.update_info = None
        print("🔕 已忽略版本更新提示")


# 全局实例
version_checker = VersionChecker()
