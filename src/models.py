#!/usr/bin/env python3
"""
GeekNews MCP 서버 데이터 모델

이 모듈은 GeekNews MCP 서버에서 사용하는 데이터 모델을 정의합니다.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class Story:
    """
    GeekNews 스토리 클래스
    
    스토리의 제목, URL, 포인트, 작성자, 시간, 댓글 수, 순위 등의 정보를 저장합니다.
    """
    title: str
    url: Optional[str]
    points: int
    author: str
    time: str
    comment_count: int
    rank: int
    
    def to_dict(self) -> Dict[str, Any]:
        """
        스토리를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 스토리 정보를 담은 딕셔너리
        """
        result = asdict(self)
        # comment_count를 commentCount로 변환 (카멜 케이스 변환)
        result["commentCount"] = result.pop("comment_count")
        return result
