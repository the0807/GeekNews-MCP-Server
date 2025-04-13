#!/usr/bin/env python3
"""
GeekNews MCP 서버 캐시 모듈

이 모듈은 GeekNews MCP 서버의 캐시 기능을 제공합니다.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import CACHE_DIR, CACHE_EXPIRY_SECONDS, logger
from src.models import Article, WeeklyNews


class CacheManager:
    """
    캐시 관리자 클래스
    
    GeekNews 데이터를 캐시하고 관리하는 기능을 제공합니다.
    """
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        """
        CacheManager 초기화
        
        Args:
            cache_dir: 캐시 디렉토리 경로
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """
        캐시 디렉토리가 존재하는지 확인하고, 없으면 생성합니다.
        """
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)
            logger.info(f"캐시 디렉토리 생성: {self.cache_dir}")
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """
        캐시 키에 해당하는 파일 경로를 반환합니다.
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            Path: 캐시 파일 경로
        """
        return self.cache_dir / f"{cache_key}.json"
    
    def save_cache(self, cache_key: str, data: Any) -> None:
        """
        데이터를 캐시에 저장합니다.
        
        Args:
            cache_key: 캐시 키
            data: 저장할 데이터
        """
        cache_path = self._get_cache_path(cache_key)
        
        # 캐시 데이터 생성
        cache_data = {
            "timestamp": int(time.time()),
            "data": data
        }
        
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"캐시 저장 완료: {cache_key}")
        except Exception as e:
            logger.error(f"캐시 저장 실패: {cache_key}, 오류: {e}", exc_info=True)
    
    def load_cache(self, cache_key: str) -> Tuple[bool, Any]:
        """
        캐시에서 데이터를 로드합니다.
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            Tuple[bool, Any]: (캐시 유효 여부, 캐시 데이터)
        """
        cache_path = self._get_cache_path(cache_key)
        
        # 캐시 파일이 없는 경우
        if not cache_path.exists():
            logger.info(f"캐시 파일 없음: {cache_key}")
            return False, None
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # 캐시 유효성 검사
            timestamp = cache_data.get("timestamp", 0)
            current_time = int(time.time())
            
            # 캐시 만료 여부 확인
            if current_time - timestamp > CACHE_EXPIRY_SECONDS:
                logger.info(f"캐시 만료됨: {cache_key}")
                return False, None
            
            logger.info(f"캐시 로드 완료: {cache_key}")
            return True, cache_data.get("data")
        except Exception as e:
            logger.error(f"캐시 로드 실패: {cache_key}, 오류: {e}", exc_info=True)
            return False, None
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """
        캐시가 유효한지 확인합니다.
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            bool: 캐시 유효 여부
        """
        cache_path = self._get_cache_path(cache_key)
        
        # 캐시 파일이 없는 경우
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # 캐시 유효성 검사
            timestamp = cache_data.get("timestamp", 0)
            current_time = int(time.time())
            
            # 캐시 만료 여부 확인
            return current_time - timestamp <= CACHE_EXPIRY_SECONDS
        except Exception:
            return False
    
    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        캐시를 삭제합니다.
        
        Args:
            cache_key: 삭제할 캐시 키 (None인 경우 모든 캐시 삭제)
        """
        if cache_key:
            # 특정 캐시만 삭제
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"캐시 삭제 완료: {cache_key}")
        else:
            # 모든 캐시 삭제
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("모든 캐시 삭제 완료")
    
    def get_articles_cache(self, article_type: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        아티클 캐시를 로드합니다.
        
        Args:
            article_type: 아티클 유형 (top, new, ask, show)
            
        Returns:
            Tuple[bool, List[Dict[str, Any]]]: (캐시 유효 여부, 아티클 목록)
        """
        cache_key = f"articles_{article_type}"
        return self.load_cache(cache_key)
    
    def save_articles_cache(self, article_type: str, articles: List[Dict[str, Any]]) -> None:
        """
        아티클 캐시를 저장합니다.
        
        Args:
            article_type: 아티클 유형 (top, new, ask, show)
            articles: 아티클 목록
        """
        cache_key = f"articles_{article_type}"
        self.save_cache(cache_key, articles)
    
    def get_weekly_news_cache(self, weekly_id: str = "latest") -> Tuple[bool, Dict[str, Any]]:
        """
        주간 뉴스 캐시를 로드합니다.
        
        Args:
            weekly_id: 주간 뉴스 ID (빈 문자열인 경우 "latest" 사용)
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (캐시 유효 여부, 주간 뉴스 정보)
        """
        cache_key = f"weekly_{weekly_id if weekly_id else 'latest'}"
        return self.load_cache(cache_key)
    
    def save_weekly_news_cache(self, weekly_news: Dict[str, Any], weekly_id: str = "") -> None:
        """
        주간 뉴스 캐시를 저장합니다.
        
        Args:
            weekly_news: 주간 뉴스 정보
            weekly_id: 주간 뉴스 ID (빈 문자열인 경우 weekly_news에서 ID 추출)
        """
        if not weekly_id and weekly_news.get("id"):
            weekly_id = weekly_news["id"]
        
        cache_key = f"weekly_{weekly_id if weekly_id else 'latest'}"
        self.save_cache(cache_key, weekly_news)
        
        # 최신 주간 뉴스인 경우 latest 캐시도 업데이트
        if not weekly_id or weekly_id == "latest":
            self.save_cache("weekly_latest", weekly_news)
