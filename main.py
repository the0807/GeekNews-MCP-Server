#!/usr/bin/env python3
"""
GeekNews MCP 서버 메인 모듈

이 모듈은 GeekNews MCP 서버의 진입점입니다.
"""

import argparse
import logging
import sys

from src.config import logger, setup_logging
from src.server import GeekNewsServer, setup_signal_handlers


def parse_args() -> argparse.Namespace:
    """
    명령줄 인수를 파싱합니다.
    
    Returns:
        argparse.Namespace: 파싱된 인수
    """
    parser = argparse.ArgumentParser(description="GeekNews MCP 서버")
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="디버그 모드 활성화"
    )
    
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="시작 시 캐시 강제 갱신"
    )
    
    parser.add_argument(
        "--server-name",
        type=str,
        default="geeknews-server",
        help="MCP 서버 이름"
    )
    
    return parser.parse_args()


def main() -> None:
    """
    메인 함수
    
    GeekNews MCP 서버를 생성하고 실행합니다.
    """
    # 명령줄 인수 파싱
    args = parse_args()
    
    # 디버그 모드 설정
    if args.debug:
        logger = setup_logging(level=logging.DEBUG)
        logger.debug("디버그 모드가 활성화되었습니다.")
    
    try:
        # 서버 생성
        server = GeekNewsServer(server_name=args.server_name)
        
        # 시그널 핸들러 설정
        setup_signal_handlers(server)
        
        # 캐시 강제 갱신
        if args.refresh:
            logger.info("캐시 강제 갱신 중...")
            server.cache_manager.clear_cache()
        
        # 서버 실행
        print(f"GeekNews MCP 서버({args.server_name})가 실행 중입니다. Ctrl+C를 눌러 종료하세요.")
        server.run()
    except Exception as e:
        logger.error(f"서버 초기화 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
