from __future__ import annotations

import argparse
import logging
import sys

from pipeline.candidate_discovery import CandidateDiscoveryPipeline
from pipeline.evidence_collection import EvidenceCollectionPipeline
from pipeline.classification import ClassificationPipeline
from pipeline.description_generation import DescriptionGenerationPipeline
from pipeline.supabase_publish import SupabasePublishPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RooftopMood DataCollector - Kakao Local + Daum Blog V2")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("discover", help="Kakao Local에서 루프탑/뷰 카페 후보 수집 + 지역 검증 + 중복 제거")
    evidence = sub.add_parser("evidence", help="Kakao Daum Blog Search에서 후기 Evidence 수집")
    evidence.add_argument("--limit", type=int, default=None, help="처음 N개 후보만 Evidence 수집")
    classify = sub.add_parser("classify", help="Kakao Local + 블로그 Evidence 기반 Rooftop/View 분류")
    classify.add_argument("--limit", type=int, default=None, help="처음 N개 후보만 분류")
    sub.add_parser("describe", help="블로그/위치/뷰 분류 기반 DB 저장용 설명 + 뷰 방향 생성")

    publish = sub.add_parser("publish", help="cafe_db_ready.csv를 Supabase 운영 DB에 upsert")
    publish.add_argument("--dry-run", action="store_true", help="실제 저장 없이 적재 대상 개수만 확인")
    publish.add_argument("--include-review", action="store_true", help="PROBABLE/설명 검토 필요 카페도 포함")
    publish.add_argument("--limit", type=int, default=None, help="처음 N개 적재 대상만 처리")

    all_parser = sub.add_parser("all", help="discover → evidence → classify → describe 연속 실행")
    all_parser.add_argument("--limit", type=int, default=None, help="처음 N개 후보로 테스트 파이프라인 실행")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_args()
    try:
        if args.command == "discover":
            CandidateDiscoveryPipeline().run()
        elif args.command == "evidence":
            EvidenceCollectionPipeline().run(limit=args.limit)
        elif args.command == "classify":
            ClassificationPipeline().run(limit=args.limit)
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
            EvidenceCollectionPipeline().run(limit=args.limit)
            ClassificationPipeline().run(limit=args.limit)
            DescriptionGenerationPipeline().run()
        return 0
    except Exception as exc:
        logging.exception("DataCollector 실패: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
