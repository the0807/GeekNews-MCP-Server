#!/usr/bin/env python3
"""
GeekNews MCP 서버 스케줄러 모듈

이 모듈은 GeekNews MCP 서버의 스케줄링 기능을 제공합니다.
"""

import threading
import time
from typing import Any, Callable, Dict, List, Optional

from src.cache import CacheManager
from src.client import GeekNewsClient
from src.config import SCHEDULER_INTERVAL_SECONDS, VALID_ARTICLE_TYPES, logger
from src.parser import ArticleParser


class DataRefreshScheduler:
    """
    데이터 갱신 스케줄러 클래스
    
    주기적으로 GeekNews 데이터를 갱신하는 스케줄러를 제공합니다.
    """
    
    def __init__(
        self,
        client: GeekNewsClient,
        parser: ArticleParser,
        cache_manager: CacheManager,
        interval: int = SCHEDULER_INTERVAL_SECONDS
    ):
        """
        DataRefreshScheduler 초기화
        
        Args:
            client: GeekNewsClient 인스턴스
            parser: ArticleParser 인스턴스
            cache_manager: CacheManager 인스턴스
            interval: 스케줄러 실행 간격 (초)
        """
        self.client = client
        self.parser = parser
        self.cache_manager = cache_manager
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """
        스케줄러를 시작합니다.
        """
        if self.running:
            logger.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("데이터 갱신 스케줄러가 시작되었습니다.")
        
        # 초기 데이터 갱신
        self.refresh_all_data()
    
    def stop(self) -> None:
        """
        스케줄러를 중지합니다.
        """
        if not self.running:
            logger.warning("스케줄러가 실행 중이 아닙니다.")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("데이터 갱신 스케줄러가 중지되었습니다.")
    
    def _run(self) -> None:
        """
        스케줄러 실행 루프
        """
        while self.running:
            try:
                # 캐시 유효성 검사 및 필요시 갱신
                self._check_and_refresh_caches()
                
                # 다음 실행까지 대기
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
            except Exception as e:
                logger.error(f"스케줄러 실행 중 오류 발생: {e}", exc_info=True)
                time.sleep(60)  # 오류 발생 시 1분 대기 후 재시도
    
    def _check_and_refresh_caches(self) -> None:
        """
        모든 캐시의 유효성을 검사하고 필요시 갱신합니다.
        """
        logger.info("캐시 유효성 검사 중...")
        
        # 아티클 캐시 검사
        for article_type in VALID_ARTICLE_TYPES:
            cache_key = f"articles_{article_type}"
            if not self.cache_manager.is_cache_valid(cache_key):
                logger.info(f"{article_type} 아티클 캐시 갱신 중...")
                self.refresh_articles(article_type)
        
        # 주간 뉴스 캐시 검사
        if not self.cache_manager.is_cache_valid("weekly_latest"):
            logger.info("최신 주간 뉴스 캐시 갱신 중...")
            self.refresh_weekly_news()
    
    def refresh_articles(self, article_type: str) -> List[Dict[str, Any]]:
        """
        특정 유형의 아티클 데이터를 갱신합니다.
        
        Args:
            article_type: 아티클 유형 (top, new, ask, show)
            
        Returns:
            List[Dict[str, Any]]: 갱신된 아티클 목록
        """
        try:
            # HTML 가져오기
            html = self.client.fetch_articles(article_type)
            
            # 아티클 파싱
            articles = self.parser.parse_articles(html)
            
            # 아티클 딕셔너리 변환
            article_dicts = [article.to_dict() for article in articles]
            
            # 캐시 저장
            self.cache_manager.save_articles_cache(article_type, article_dicts)
            
            logger.info(f"{article_type} 아티클 캐시 갱신 완료 ({len(article_dicts)}개)")
            return article_dicts
        except Exception as e:
            logger.error(f"{article_type} 아티클 갱신 실패: {e}", exc_info=True)
            return []
    
    def refresh_weekly_news(self, weekly_id: str = "") -> Dict[str, Any]:
        """
        주간 뉴스 데이터를 갱신합니다.
        
        Args:
            weekly_id: 주간 뉴스 ID (빈 문자열인 경우 가장 최근 주간 뉴스를 가져옴)
            
        Returns:
            Dict[str, Any]: 갱신된 주간 뉴스 정보
        """
        try:
            # HTML 가져오기
            html = self.client.fetch_weekly_news(weekly_id)
            
            # 주간 뉴스 파싱
            weekly_news = self.parser.parse_weekly_news(html)
            
            # 주간 뉴스 딕셔너리 변환
            weekly_dict = weekly_news.to_dict()
            
            # 캐시 저장
            self.cache_manager.save_weekly_news_cache(weekly_dict, weekly_id)
            
            logger.info(f"주간 뉴스 캐시 갱신 완료 (ID: {weekly_dict.get('id', 'latest')})")
            return weekly_dict
        except Exception as e:
            logger.error(f"주간 뉴스 갱신 실패: {e}", exc_info=True)
            return {
                "title": "GeekNews Weekly",
                "number": 0,
                "id": weekly_id if weekly_id else "",
                "content": "주간 뉴스를 가져오는 중 오류가 발생했습니다.",
                "url": f"{self.client.base_url}/weekly" + (f"/{weekly_id}" if weekly_id else ""),
                "items": []
            }
    
    def refresh_all_data(self) -> None:
        """
        모든 데이터를 갱신합니다.
        """
        logger.info("모든 데이터 갱신 중...")
        
        # 모든 유형의 아티클 갱신
        for article_type in VALID_ARTICLE_TYPES:
            self.refresh_articles(article_type)
        
        # 주간 뉴스 갱신
        self.refresh_weekly_news()
        
        logger.info("모든 데이터 갱신 완료")
