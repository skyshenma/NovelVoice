
from typing import List, Optional

class TextSplitter:
    """
    智能文本切分器
    采用递归切分策略，优先在段落、长句结束符处切分，避免在此处截断。
    """
    
    def __init__(self, separators: Optional[List[str]] = None):
        if separators is None:
            self.separators = [
                "\n\n",  # 段落
                "\n",    # 换行
                "。",    # 句号 (中文)
                "！",    # 感叹号 (中文)
                "？",    # 问号 (中文)
                "；",    # 分号 (中文)
                ". ",    # 句号 (英文+空格)
                "! ",    # 感叹号 (英文+空格)
                "? ",    # 问号 (英文+空格)
                "; ",    # 分号 (英文+空格)
                " ",     # 空格
                ""       # 字符级 (最后防线)
            ]
        else:
            self.separators = separators

    def split_text(self, text: str, max_chars: int) -> List[str]:
        """
        递归切分文本，确保每段长度不超过 max_chars
        """
        final_chunks = []
        good_splits = self._recursive_split(text, self.separators, max_chars)
        
        # 合并过小的片段 (优化 TTS 调用)
        current_chunk = ""
        for split in good_splits:
            if len(current_chunk) + len(split) <= max_chars:
                current_chunk += split
            else:
                if current_chunk:
                    final_chunks.append(current_chunk)
                current_chunk = split
        
        if current_chunk:
            final_chunks.append(current_chunk)
            
        return final_chunks

    def _recursive_split(self, text: str, separators: List[str], max_chars: int) -> List[str]:
        """
        核心递归逻辑
        """
        # 1. 如果文本已经足够短，直接返回
        if len(text) <= max_chars:
            return [text]
            
        # 2. 如果没有分隔符可用，强制切分 (最后防线)
        if not separators:
            return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
            
        # 3. 尝试使用当前分隔符
        separator = separators[0]
        next_separators = separators[1:]
        
        # 特殊处理空分隔符 (字符级切分)
        if separator == "":
             return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
             
        # 按分隔符切分 (保留分隔符)
        # 注意：这里简单的 split 会丢失分隔符，我们需要保留它以便 TTS 停顿自然
        # 策略：将分隔符附在前半部分
        
        splits = []
        parts = text.split(separator)
        
        # 重新组合 parts，加上 separator
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                splits.append(part + separator)
            elif part: # 最后一部分，如果不为空
                splits.append(part)
                
        # 4. 检查切分结果
        final_chunks = []
        good_splits = []
        
        # 尝试合并当前层级的切分结果，看是否满足 max_chars
        current_merge = ""
        for s in splits:
            if len(s) > max_chars:
                # 当前片段本身就超长 -> 需要用下一个分隔符继续递归切分
                # 先把之前累积的 current_merge 放入
                if current_merge:
                    final_chunks.append(current_merge)
                    current_merge = ""
                    
                # 递归处理这个超长片段
                sub_chunks = self._recursive_split(s, next_separators, max_chars)
                final_chunks.extend(sub_chunks)
            else:
                # 当前片段小于 max_chars，尝试合并
                if len(current_merge) + len(s) <= max_chars:
                    current_merge += s
                else:
                    final_chunks.append(current_merge)
                    current_merge = s
                    
        if current_merge:
            final_chunks.append(current_merge)
            
        return final_chunks
