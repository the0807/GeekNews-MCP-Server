#!/usr/bin/env python3
"""
GeekNews 파서

이 모듈은 GeekNews 웹사이트의 HTML을 파싱하여 아티클 정보를 추출하는 기능을 제공합니다.
"""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.config import BASE_URL, logger
from src.models import Article, WeeklyNews


class ArticleParser:
    """
    GeekNews 아티클 파서 클래스
    
    GeekNews 웹사이트의 HTML을 파싱하여 아티클 정보를 추출합니다.
    """
    
    def __init__(self, base_url: str = BASE_URL):
        """
        ArticleParser 초기화
        
        Args:
            base_url: GeekNews 웹사이트 기본 URL
        """
        self.base_url = base_url
    
    def parse_articles(self, html: str) -> List[Article]:
        """
        HTML에서 아티클 정보를 파싱합니다.
        
        Args:
            html: 파싱할 HTML
            
        Returns:
            List[Article]: 파싱된 아티클 목록
        """
        soup = BeautifulSoup(html, "html.parser")
        articles = []
        
        # topic_row 클래스를 가진 div 요소가 각 뉴스 항목을 나타냄
        for i, item in enumerate(soup.select("div.topic_row")):
            try:
                article = self._parse_article_item(item, i)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.error(f"아티클 파싱 중 오류 발생: {e}", exc_info=True)
        
        return articles
    
    def _parse_article_item(self, item: Tag, index: int) -> Optional[Article]:
        """
        개별 아티클 항목을 파싱합니다.
        
        Args:
            item: 파싱할 HTML 요소
            index: 항목 인덱스
            
        Returns:
            Optional[Article]: 파싱된 아티클 또는 None
        """
        # 순위 번호 추출
        rank = self._extract_rank(item, index)
        
        # 제목과 URL 추출
        title, url = self._extract_title_and_url(item)
        if not title:
            return None
        
        # 메타데이터 추출
        points, author, time, comment_count = self._extract_metadata(item)
        
        return Article(
            title=title,
            url=url,
            points=points,
            author=author,
            time=time,
            comment_count=comment_count,
            rank=rank
        )
    
    def _extract_rank(self, item: Tag, index: int) -> int:
        """
        순위 번호를 추출합니다.
        
        Args:
            item: 파싱할 HTML 요소
            index: 항목 인덱스
            
        Returns:
            int: 순위 번호
        """
        votenum = item.select_one(".votenum")
        if votenum and votenum.text.strip():
            try:
                return int(votenum.text.strip())
            except ValueError:
                pass
        return index + 1
    
    def _extract_title_and_url(self, item: Tag) -> Tuple[str, Optional[str]]:
        """
        제목과 URL을 추출합니다.
        
        Args:
            item: 파싱할 HTML 요소
            
        Returns:
            Tuple[str, Optional[str]]: 제목과 URL
        """
        title_element = item.select_one(".topictitle a")
        if not title_element:
            return "", None
        
        # h1 태그가 있으면 그 안의 텍스트를 가져옴
        h1 = title_element.select_one("h1")
        title = h1.text.strip() if h1 else title_element.text.strip()
        
        url = title_element.get("href")
        
        # URL이 상대 경로인 경우 절대 경로로 변환
        if url and not url.startswith(("http://", "https://")):
            url = urljoin(self.base_url, url)
        
        return title, url
    
    def _extract_metadata(self, item: Tag) -> Tuple[int, str, str, int]:
        """
        메타데이터(포인트, 작성자, 시간, 댓글 수)를 추출합니다.
        
        Args:
            item: 파싱할 HTML 요소
            
        Returns:
            Tuple[int, str, str, int]: 포인트, 작성자, 시간, 댓글 수
        """
        topicinfo = item.select_one(".topicinfo")
        if not topicinfo:
            return 0, "익명", "", 0
        
        topicinfo_text = topicinfo.text.strip()
        
        # 포인트 추출
        points = self._extract_points(topicinfo, topicinfo_text)
        
        # 작성자 추출
        author = self._extract_author(topicinfo, topicinfo_text)
        
        # 시간 추출
        time = self._extract_time(topicinfo_text)
        
        # 댓글 수 추출
        comment_count = self._extract_comment_count(topicinfo)
        
        return points, author, time, comment_count
    
    def _extract_points(self, topicinfo: Tag, topicinfo_text: str) -> int:
        """
        포인트를 추출합니다.
        
        Args:
            topicinfo: 메타데이터 HTML 요소
            topicinfo_text: 메타데이터 텍스트
            
        Returns:
            int: 포인트
        """
        points_element = topicinfo.select_one("span[id^='tp']")
        if points_element:
            try:
                return int(points_element.text.strip())
            except ValueError:
                pass
        
        # 정규 표현식으로 포인트 추출 시도
        points_match = re.search(r'(\d+)\s*points?', topicinfo_text)
        if points_match:
            try:
                return int(points_match.group(1))
            except ValueError:
                pass
        
        return 0
    
    def _extract_author(self, topicinfo: Tag, topicinfo_text: str) -> str:
        """
        작성자를 추출합니다.
        
        Args:
            topicinfo: 메타데이터 HTML 요소
            topicinfo_text: 메타데이터 텍스트
            
        Returns:
            str: 작성자
        """
        author_element = topicinfo.select_one("a[href^='/user']")
        if author_element:
            return author_element.text.strip()
        
        # 정규 표현식으로 작성자 추출 시도
        author_match = re.search(r'by\s+([^\s]+)', topicinfo_text)
        if author_match:
            return author_match.group(1)
        
        return "익명"
    
    def _extract_time(self, topicinfo_text: str) -> str:
        """
        시간을 추출합니다.
        
        Args:
            topicinfo_text: 메타데이터 텍스트
            
        Returns:
            str: 시간
        """
        time_match = re.search(r'(\d+시간전|\d+분전|\d+일전)', topicinfo_text)
        return time_match.group(1) if time_match else ""
    
    def _extract_comment_count(self, topicinfo: Tag) -> int:
        """
        댓글 수를 추출합니다.
        
        Args:
            topicinfo: 메타데이터 HTML 요소
            
        Returns:
            int: 댓글 수
        """
        comment_element = topicinfo.select_one("a.u")
        if comment_element:
            comment_text = comment_element.text.strip()
            comment_match = re.search(r'댓글\s*(\d+)개', comment_text)
            if comment_match:
                try:
                    return int(comment_match.group(1))
                except ValueError:
                    pass
        
        return 0
    
    def parse_weekly_news(self, html: str) -> WeeklyNews:
        """
        HTML에서 주간 뉴스 정보를 파싱합니다.
        
        Args:
            html: 파싱할 HTML
            
        Returns:
            WeeklyNews: 파싱된 주간 뉴스
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # 제목 추출
        title_element = soup.select_one("title")
        title = title_element.text.strip() if title_element else "GeekNews Weekly"
        
        # 번호와 ID 추출
        number = 0
        weekly_id = ""
        title_match = re.search(r'\[GN#(\d+)\]', title)
        if title_match:
            number = int(title_match.group(1))
        
        url_element = soup.select_one("meta[property='og:url']")
        if url_element:
            url = url_element.get("content", "")
            url_match = re.search(r'/weekly/(\d+)', url)
            if url_match:
                weekly_id = url_match.group(1)
        else:
            url = f"{self.base_url}/weekly"
        
        # 내용 추출 - 전체 내용을 가져오기 위해 여러 소스를 결합
        content_parts = []
        
        # 주간 뉴스 아이템 추출
        items = []
        
        # 1. 메타 설명은 제외 (사용자 요청에 따라)
        
        # 2. 설명 요소에서 내용 추출 및 링크 추출
        desc_element = soup.select_one("div.desc")
        if desc_element:
            # 내용 추출
            desc_text = desc_element.get_text(separator=" ", strip=True)
            if desc_text and desc_text not in content_parts:
                content_parts.append(desc_text)
            
            # 링크 추출
            links = desc_element.select("a")
            for i, link in enumerate(links):
                try:
                    link_title = link.text.strip()
                    link_url = link.get("href", "")
                    
                    # 빈 제목이나 URL이 없는 경우 건너뛰기
                    if not link_title or not link_url:
                        continue
                    
                    # URL이 상대 경로인 경우 절대 경로로 변환
                    if link_url and not link_url.startswith(("http://", "https://")):
                        link_url = urljoin(self.base_url, link_url)
                    
                    # URL 정보를 items에 추가
                    if not any(existing.get("url") == link_url for existing in items):
                        items.append({
                            "title": link_title,
                            "url": link_url,
                            "rank": i + 1
                        })
                except Exception as e:
                    logger.error(f"주간 뉴스 링크 파싱 중 오류 발생: {e}", exc_info=True)
        
        # 3. topics 요소에서 URL 정보 추출 코드 제거 (사용자 요청에 따라)
        topic_elements = soup.select("div.topics div.topic_row")
        
        # 4. topics 요소에서 URL 정보 추출 코드 제거 (사용자 요청에 따라)
        
        # 모든 내용을 하나의 문자열로 결합
        full_content = "\n\n".join(content_parts)
        
        # 주간 뉴스 상세 페이지와 목록 페이지에서 URL 정보를 추출하는 코드 제거 (사용자 요청에 따라)
        
        # 아이템 제한 제거
        
        # content에서 URL 정보를 추출하는 코드 제거 (사용자 요청에 따라)
        
        return WeeklyNews(
            title=title,
            number=number,
            id=weekly_id,
            content=full_content,
            url=url,
            items=items
        )
