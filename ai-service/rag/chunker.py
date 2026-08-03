"""中文感知递归分块器 — 直接采用 regent（ragent-replica）实现。

分隔符优先级：\n\n → \n → 。 → ， → 空格 → 字符级保底。
chunk_id = md5(text)[:12]；记录 start_offset/end_offset 便于回映射原文。
"""
from __future__ import annotations

import hashlib
from typing import List

from pydantic import BaseModel


class Chunk(BaseModel):
    id: str
    text: str
    start_offset: int
    end_offset: int
    chunk_index: int


class RecursiveChineseSplitter:
    """递归字符分割器（中文感知，regent 同款）。"""

    # 分隔符优先级（从高到低）
    SEPARATORS = ["\n\n", "\n", "。", "，", " ", ""]

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) 必须小于 chunk_size ({chunk_size})")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[Chunk]:
        """将长文本切分为分块。"""
        chunks: List[Chunk] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # 如果不是最后一段，尝试在分隔符处断开
            if end < text_len:
                end = self._find_split_point(text, start, end)

            chunk_text = text[start:end]
            if chunk_text.strip():
                chunk_id = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()[:12]
                chunks.append(Chunk(
                    id=chunk_id,
                    text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                    chunk_index=len(chunks),
                ))

            # 移动起点（带重叠）；防死循环：分割点与起点差 <= overlap 时放弃重叠强制前进
            if end < text_len:
                next_start = end - self.chunk_overlap
                if next_start <= start:
                    next_start = end
                start = next_start
            else:
                start = text_len

        return chunks

    def _find_split_point(self, text: str, start: int, preferred_end: int) -> int:
        """在 [start, preferred_end] 范围内找最佳分隔位置。"""
        for sep in self.SEPARATORS:
            if not sep:
                return preferred_end  # 字符级保底
            # 从 preferred_end 往前找
            pos = text.rfind(sep, start, preferred_end)
            if pos != -1 and pos > start:
                return pos + len(sep)
        return preferred_end
