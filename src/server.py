#!/usr/bin/env python3
"""
GeekNews MCP 서버

이 모듈은 GeekNews 웹사이트에서 아티클을 가져오는 MCP 서버를 구현합니다.
"""

import signal
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from src.client import GeekNewsClient
from src.config import BASE_URL, DEFAULT_ARTICLE_LIMIT, MAX_ARTICLES, VALID_ARTICLE_TYPES, logger
from src.models import Article, WeeklyNews
from src.parser import ArticleParser


class GeekNewsServer:
    """
    GeekNews MCP 서버 클래스
    
    GeekNews 웹사이트에서 아티클을 가져오는 MCP 서버를 구현합니다.
    """
    
    def __init__(self, server_name: str = "geeknews-server", base_url: str = BASE_URL):
        """
        GeekNewsServer 초기화
        
        Args:
            server_name: MCP 서버 이름
            base_url: GeekNews 웹사이트 기본 URL
        """
        self.mcp = FastMCP(server_name)
        self.client = GeekNewsClient(base_url)
        self.parser = ArticleParser(base_url)
        self.setup_tools()
    
    def run(self) -> None:
        """
        MCP 서버를 실행합니다.
        """
        try:
            logger.info("GeekNews MCP 서버가 실행 중입니다")
            self.mcp.run()
        except Exception as e:
            logger.error(f"서버 실행 중 오류 발생: {e}", exc_info=True)
            sys.exit(1)
    
    def setup_tools(self) -> None:
        """
        MCP 도구를 설정합니다.
        """
        self._setup_get_articles_tool()
        self._setup_get_weekly_news_tool()
    
    def _setup_get_articles_tool(self) -> None:
        """
        get_articles 도구를 설정합니다.
        """
        @self.mcp.tool()
        def get_articles(type: str = "top", limit: int = DEFAULT_ARTICLE_LIMIT) -> List[Dict[str, Any]]:
            """
            GeekNews에서 아티클을 가져오는 도구
            
            Args:
                type: 아티클 유형 (top, new, ask, show)
                limit: 반환할 아티클 수 (최대 30)
            
            Returns:
                List[Dict[str, Any]]: 아티클 목록
                
            Raises:
                ValueError: 유효하지 않은 아티클 유형이 지정된 경우
            """
            return self._get_articles(type, limit)
    
    def _setup_get_weekly_news_tool(self) -> None:
        """
        get_weekly_news 도구를 설정합니다.
        """
        @self.mcp.tool()
        def get_weekly_news(weekly_id: str = "") -> Dict[str, Any]:
            """
            GeekNews에서 주간 뉴스를 가져오는 도구
            
            Args:
                weekly_id: 주간 뉴스 ID (빈 문자열인 경우 가장 최근 주간 뉴스를 가져옴)
                
            Returns:
                Dict[str, Any]: 주간 뉴스 정보
            """
            return self._get_weekly_news(weekly_id)
    
    def _get_weekly_news(self, weekly_id: str = "") -> Dict[str, Any]:
        """
        GeekNews에서 주간 뉴스를 가져옵니다.
        
        Args:
            weekly_id: 주간 뉴스 ID (빈 문자열인 경우 가장 최근 주간 뉴스를 가져옴)
            
        Returns:
            Dict[str, Any]: 주간 뉴스 정보
        """
        try:
            # HTML 가져오기
            html = self.client.fetch_weekly_news(weekly_id)
            
            # 주간 뉴스 파싱
            weekly_news = self.parser.parse_weekly_news(html)
            
            # 결과 반환
            return weekly_news.to_dict()
        except Exception as e:
            logger.error(f"주간 뉴스 가져오기 실패: {e}", exc_info=True)
            return {
                "title": "GeekNews Weekly",
                "number": 0,
                "id": weekly_id if weekly_id else "",
                "content": "주간 뉴스를 가져오는 중 오류가 발생했습니다.",
                "url": f"{self.client.base_url}/weekly" + (f"/{weekly_id}" if weekly_id else ""),
                "items": []
            }
    
    def _get_articles(self, type: str, limit: int) -> List[Dict[str, Any]]:
        """
        GeekNews에서 아티클을 가져옵니다.
        
        Args:
            type: 아티클 유형 (top, new, ask, show)
            limit: 반환할 아티클 수 (최대 30)
        
        Returns:
            List[Dict[str, Any]]: 아티클 목록
        """
        # 입력 유효성 검사
        if type not in VALID_ARTICLE_TYPES:
            raise ValueError(
                f"유효하지 않은 아티클 유형: {type}. "
                f"다음 중 하나여야 합니다: {', '.join(VALID_ARTICLE_TYPES)}"
            )
        
        # 아티클 수 제한
        limit = max(1, min(limit, MAX_ARTICLES))
        
        try:
            # HTML 가져오기
            html = self.client.fetch_articles(type)
            
            # 아티클 파싱
            articles = self.parser.parse_articles(html)
            
            # 결과 반환
            return [article.to_dict() for article in articles[:limit]]
        except Exception as e:
            logger.error(f"아티클 가져오기 실패: {e}", exc_info=True)
            return []


def setup_signal_handlers(server: GeekNewsServer) -> None:
    """
    시그널 핸들러를 설정합니다.
    
    Args:
        server: GeekNewsServer 인스턴스
    """
    def handle_signal(sig: int, frame: Any) -> None:
        """
        시그널 핸들러
        
        Args:
            sig: 시그널 번호
            frame: 현재 스택 프레임
        """
        logger.info("서버를 종료합니다...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
