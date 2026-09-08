from __future__ import annotations

import argparse
import logging
import sys

from pipeline.candidate_discovery import CandidateDiscoveryPipeline
from pipeline.evidence_collection import EvidenceCollectionPipeline
from pipeline.classification import ClassificationPipeline
from pipeline.description_generation import DescriptionGenerationPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RooftopMood DataCollector")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("discover", help="Kakao/Naver Local에서 루프탑 카페 후보 수집 + 중복 제거")

    evidence = sub.add_parser("evidence", help="Naver Blog API로 후보별 루프탑/뷰 근거 수집")
    evidence.add_argument("--limit", type=int, default=None, help="처음 N개 후보만 테스트")

    sub.add_parser("classify", help="Evidence 기반 Rooftop/View 분류 + 기타 뷰 후보 발견")
    sub.add_parser("describe", help="외부 LLM 없이 DB 저장용 고정 1문장 뷰 설명 생성")

    all_cmd = sub.add_parser("all", help="discover → evidence → classify → describe 연속 실행")
    all_cmd.add_argument("--limit", type=int, default=None, help="Evidence 수집 대상 N개 제한")
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
            ClassificationPipeline().run()
        elif args.command == "describe":
            DescriptionGenerationPipeline().run()
        elif args.command == "all":
            CandidateDiscoveryPipeline().run()
            EvidenceCollectionPipeline().run(limit=args.limit)
            ClassificationPipeline().run()
            DescriptionGenerationPipeline().run()
        return 0
    except Exception as exc:
        logging.exception("DataCollector 실패: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
