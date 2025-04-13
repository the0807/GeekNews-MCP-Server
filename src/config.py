#!/usr/bin/env python3
"""
GeekNews MCP 서버 설정

이 모듈은 GeekNews MCP 서버의 설정과 상수를 정의합니다.
"""

import logging
import os
import sys
from pathlib import Path

# 기본 URL
BASE_URL = "https://news.hada.io"

# 유효한 아티클 유형
VALID_ARTICLE_TYPES = ["top", "new", "ask", "show"]

# 아티클 관련 상수
MAX_ARTICLES = 30
DEFAULT_ARTICLE_LIMIT = 10

# 네트워크 요청 관련 상수
REQUEST_TIMEOUT = 10  # 초

# 캐시 관련 설정
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "geeknews-mcp")
CACHE_EXPIRY_SECONDS = 24 * 60 * 60  # 24시간 (하루)

# 스케줄러 관련 설정
SCHEDULER_INTERVAL_SECONDS = 60 * 60  # 1시간마다 캐시 유효성 검사

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
        format='%(asctime)s - %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    return logging.getLogger("geeknews-server")

# 전역 로거 객체
logger = setup_logging()
