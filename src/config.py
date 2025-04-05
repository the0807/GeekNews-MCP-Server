#!/usr/bin/env python3
"""
GeekNews MCP 서버 설정

이 모듈은 GeekNews MCP 서버의 설정과 상수를 정의합니다.
"""

import logging
import sys

# 기본 URL
BASE_URL = "https://news.hada.io"

# 유효한 아티클 유형
VALID_ARTICLE_TYPES = ["top", "new", "ask", "show"]

# 아티클 관련 상수
MAX_ARTICLES = 30
DEFAULT_ARTICLE_LIMIT = 10

# 네트워크 요청 관련 상수
REQUEST_TIMEOUT = 10  # 초

# 로깅 설정
def setup_logging(level=logging.WARNING):
    """
    로깅 설정을 초기화합니다.
    
    Args:
        level: 로그 레벨 (기본값: WARNING)
    
    Returns:
        logging.Logger: 로거 객체
    """
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    return logging.getLogger("geeknews-server")

# 전역 로거 객체
logger = setup_logging()
