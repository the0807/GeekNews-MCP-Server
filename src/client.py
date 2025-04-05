#!/usr/bin/env python3
"""
GeekNews 클라이언트

이 모듈은 GeekNews 웹사이트에서 데이터를 가져오는 HTTP 클라이언트를 제공합니다.
"""

from urllib.parse import urljoin

import requests

from src.config import BASE_URL, REQUEST_TIMEOUT, logger


class GeekNewsClient:
    """
    GeekNews HTTP 클라이언트 클래스
    
    GeekNews 웹사이트에서 데이터를 가져오는 HTTP 클라이언트를 제공합니다.
    """
    
    def __init__(self, base_url: str = BASE_URL):
        """
        GeekNewsClient 초기화
        
        Args:
            base_url: GeekNews 웹사이트 기본 URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeekNews MCP Server/1.0',
        })
    
    def fetch_stories(self, story_type: str = "top") -> str:
        """
        GeekNews 웹사이트에서 스토리 목록 HTML을 가져옵니다.
        
        Args:
            story_type: 스토리 유형 (top, new, ask, show)
            
        Returns:
            str: 웹사이트 HTML
            
        Raises:
            requests.RequestException: HTTP 요청 실패 시
        """
        url = self.base_url
        if story_type != "top":
            url = f"{self.base_url}/{story_type}"
        
        logger.info(f"스토리 목록 가져오기: {url}")
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
