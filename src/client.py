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
    
    def fetch_articles(self, article_type: str = "top") -> str:
        """
        GeekNews 웹사이트에서 아티클 목록 HTML을 가져옵니다.
        
        Args:
            article_type: 아티클 유형 (top, new, ask, show)
            
        Returns:
            str: 웹사이트 HTML
            
        Raises:
            requests.RequestException: HTTP 요청 실패 시
        """
        url = self.base_url
        if article_type != "top":
            url = f"{self.base_url}/{article_type}"
        
        logger.info(f"아티클 목록 가져오기: {url}")
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    
    def fetch_weekly_news(self, weekly_id: str = "") -> str:
        """
        GeekNews 웹사이트에서 주간 뉴스 HTML을 가져옵니다.
        
        Args:
            weekly_id: 주간 뉴스 ID (빈 문자열인 경우 가장 최근 주간 뉴스를 가져옴)
            
        Returns:
            str: 웹사이트 HTML
            
        Raises:
            requests.RequestException: HTTP 요청 실패 시
        """
        # 주간 뉴스 목록 페이지 URL
        weekly_list_url = f"{self.base_url}/weekly"
        
        # 특정 주간 뉴스 ID가 제공되지 않은 경우 가장 최근 주간 뉴스 ID를 찾음
        if not weekly_id:
            logger.info(f"주간 뉴스 목록 가져오기: {weekly_list_url}")
            response = self.session.get(weekly_list_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # 첫 페이지에서 가장 최근 주간 뉴스의 ID를 추출
            html = response.text
            import re
            latest_weekly_id_match = re.search(r'<a href=\'/weekly/(\d+)\' class=\'u\'>', html)
            
            if not latest_weekly_id_match:
                logger.error("최근 주간 뉴스 ID를 찾을 수 없습니다.")
                return html
            
            weekly_id = latest_weekly_id_match.group(1)
            logger.info(f"가장 최근 주간 뉴스 ID: {weekly_id}")
        
        # 주간 뉴스 상세 페이지 가져오기
        detail_url = f"{self.base_url}/weekly/{weekly_id}"
        logger.info(f"주간 뉴스 상세 가져오기: {detail_url}")
        
        try:
            detail_response = self.session.get(detail_url, timeout=REQUEST_TIMEOUT)
            detail_response.raise_for_status()
            return detail_response.text
        except requests.RequestException as e:
            logger.error(f"주간 뉴스 상세 가져오기 실패: {e}", exc_info=True)
            # 실패 시 주간 뉴스 목록 페이지 반환
            return self.session.get(weekly_list_url, timeout=REQUEST_TIMEOUT).text
