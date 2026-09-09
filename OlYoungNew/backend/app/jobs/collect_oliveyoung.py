from __future__ import annotations

import argparse
import sys
import traceback

from ..collectors.oliveyoung import OliveYoungClient
from ..config import OLIVEYOUNG_MAX_PAGES
from ..scoring import calculate_reaction_score
from ..storage import SQLiteStore


def run(*, pages: int, use_selenium: bool | None = None) -> int:
    store = SQLiteStore()
    run_id = store.start_run()
    products_found = 0
    try:
        print(f"[OlYoungNew] 올리브영 신상품순 수집 시작 | pages={pages}")
        with OliveYoungClient(use_selenium=use_selenium) as client:
            products = client.collect(pages=pages)
        if not products:
            raise RuntimeError("상품을 한 건도 수집하지 못했습니다. 페이지 구조/접속 상태를 확인하세요.")
        products_found = store.save_products(products)
        print(f"[OlYoungNew] snapshot 저장 완료 | products={products_found}")
        score_count = 0
        for goods_no in store.list_latest_snapshot_goods():
            latest, previous = store.get_latest_and_previous_snapshots(goods_no)
            if latest is None:
                continue
            store.save_reaction_score(goods_no, calculate_reaction_score(latest, previous))
            score_count += 1
        store.finish_run(run_id, status="SUCCESS", products_found=products_found)
        print(f"[OlYoungNew] 반응지수 계산 완료 | scores={score_count}")
        print(f"[OlYoungNew] DB: {store.path}")
        return 0
    except Exception as exc:
        store.finish_run(run_id, status="FAILED", products_found=products_found, error_message=str(exc))
        print(f"[ERROR] {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="올영뉴 올리브영 신상 snapshot 수집기")
    parser.add_argument("--pages", type=int, default=OLIVEYOUNG_MAX_PAGES)
    parser.add_argument("--selenium", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(pages=max(1, args.pages), use_selenium=True if args.selenium else None))


if __name__ == "__main__":
    main()
