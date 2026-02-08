import pathlib
from .base import BaseParser
from .txt import TxtParser
from .epub import EpubParser

class ParserFactory:
    @staticmethod
    def get_parser(file_path: str) -> BaseParser:
        path = pathlib.Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.txt':
            return TxtParser()
        elif suffix == '.epub':
            return EpubParser()
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
