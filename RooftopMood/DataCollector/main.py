from __future__ import annotations

import argparse
import logging
import sys

from pipeline.candidate_discovery import CandidateDiscoveryPipeline
from pipeline.classification import ClassificationPipeline
from pipeline.description_generation import DescriptionGenerationPipeline
from pipeline.supabase_publish import SupabasePublishPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RooftopMood DataCollector - Kakao Only MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("discover", help="Kakao Local에서 루프탑/뷰 카페 후보 수집 + 중복 제거")
    sub.add_parser("classify", help="Kakao 검색 적중 패턴 기반 Rooftop/View 분류")
    sub.add_parser("describe", help="위치/뷰 분류 기반 DB 저장용 1문장 설명 + 뷰 방향 생성")

    publish = sub.add_parser("publish", help="cafe_db_ready.csv를 Supabase 운영 DB에 upsert")
    publish.add_argument("--dry-run", action="store_true", help="실제 저장 없이 적재 대상 개수만 확인")
    publish.add_argument("--include-review", action="store_true", help="설명 검토 필요 카페도 포함")
    publish.add_argument("--limit", type=int, default=None, help="처음 N개 적재 대상만 처리")

    sub.add_parser("all", help="discover → classify → describe 연속 실행")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_args()
    try:
        if args.command == "discover":
            CandidateDiscoveryPipeline().run()
        elif args.command == "classify":
            ClassificationPipeline().run()
        elif args.command == "describe":
            DescriptionGenerationPipeline().run()
        elif args.command == "publish":
            SupabasePublishPipeline().run(
                dry_run=args.dry_run,
                include_review=args.include_review,
                limit=args.limit,
            )
        elif args.command == "all":
            CandidateDiscoveryPipeline().run()
            ClassificationPipeline().run()
            DescriptionGenerationPipeline().run()
        return 0
    except Exception as exc:
        logging.exception("DataCollector 실패: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
