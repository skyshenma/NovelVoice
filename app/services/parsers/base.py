from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pathlib

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: pathlib.Path) -> List[Dict[str, Any]]:
        """
        Parse a book file into a list of chapters.
        
        Args:
            file_path: Path to the book file.
            
        Returns:
            List of dictionaries, each containing:
            - id: int
            - title: str
            - content: str
            - status: str (e.g. 'pending')
            - audio_path: str (empty)
        """
        pass
