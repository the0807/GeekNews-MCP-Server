#!/usr/bin/env python3
"""
GeekNews MCP 서버 메인 모듈

이 모듈은 GeekNews MCP 서버의 진입점입니다.
"""

import sys

from src.config import logger
from src.server import GeekNewsServer, setup_signal_handlers

# 전역 서버 객체 생성
server = GeekNewsServer()

def main() -> None:
    """
    메인 함수
    
    GeekNews MCP 서버를 생성하고 실행합니다.
    """
    try:
        # 시그널 핸들러 설정
        setup_signal_handlers(server)
        
        # 서버 실행
        print("GeekNews MCP 서버가 실행 중입니다. Ctrl+C를 눌러 종료하세요.")
        server.run()
    except Exception as e:
        logger.error(f"서버 초기화 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
