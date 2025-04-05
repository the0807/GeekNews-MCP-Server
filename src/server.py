#!/usr/bin/env python3
"""
GeekNews MCP 서버

이 모듈은 GeekNews 웹사이트에서 아티클을 가져오는 MCP 서버를 구현합니다.
"""

import signal
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
import mcp.types as types

from src.client import GeekNewsClient
from src.config import BASE_URL, DEFAULT_ARTICLE_LIMIT, MAX_ARTICLES, VALID_ARTICLE_TYPES, logger
from src.models import Article
from src.parser import ArticleParser


# 사용 가능한 프롬프트 정의
PROMPTS = {
    "geeknews-articles": types.Prompt(
        name="geeknews-articles",
        description="GeekNews 아티클 정보에 URL을 포함합니다",
        arguments=[],
    )
}


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
        MCP 도구와 프롬프트를 설정합니다.
        """
        self._setup_get_articles_tool()
        self._setup_prompts()
    
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
    
    def _setup_prompts(self) -> None:
        """
        MCP 프롬프트를 설정합니다.
        """
        @self.mcp.prompt()
        def list_prompts() -> List[types.Prompt]:
            """
            사용 가능한 프롬프트 목록을 반환합니다.
            
            Returns:
                List[types.Prompt]: 프롬프트 목록
            """
            return list(PROMPTS.values())
        
        @self.mcp.prompt()
        def get_prompt(name: str) -> Dict[str, Any]:
            """
            프롬프트를 가져옵니다.
            
            Args:
                name: 프롬프트 이름
                
            Returns:
                Dict[str, Any]: 프롬프트 결과
            """
            if name not in PROMPTS:
                raise ValueError(f"프롬프트를 찾을 수 없습니다: {name}")
            
            if name == "geeknews-articles":
                return {
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": "응답에는 반드시 각 아티클의 제목, URL, 그리고 간단한 설명을 포함해야 합니다. 모든 URL은 반드시 포함해주세요."
                            }
                        }
                    ]
                }
            
            raise ValueError("프롬프트 구현을 찾을 수 없습니다")
    
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
