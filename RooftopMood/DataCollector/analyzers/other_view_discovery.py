from __future__ import annotations

from collections import defaultdict
import re

from analyzers.evidence_utils import compact_text, relevance_multiplier


class OtherViewDiscovery:
    """기존 4종 외 반복 등장하는 view 표현을 후보로 수집한다.

    자동으로 앱 카테고리에 추가하지 않고 사람이 검토할 후보 CSV만 만든다.
    """

    KNOWN = {
        "한강", "한강뷰", "리버", "리버뷰", "시티", "시티뷰", "도심", "도심뷰", "빌딩", "빌딩뷰",
        "궁궐", "궁궐뷰", "경복궁", "경복궁뷰", "창덕궁", "창덕궁뷰", "덕수궁", "덕수궁뷰",
        "숲", "숲뷰", "서울숲", "서울숲뷰", "녹지", "녹지뷰",
    }
    STOP = {
        "오션", "바다", "제주", "부산", "뷰", "좋은", "예쁜", "멋진", "최고", "탁트인", "탁 트인",
        "카페", "루프탑", "테라스", "야외", "야경",
    }
    LANDMARK_PATTERNS = {
        "남산타워": ["남산타워", "n서울타워", "n 서울타워", "서울타워"],
        "북한산": ["북한산"],
        "한양도성": ["한양도성", "서울성곽", "성곽뷰", "성곽 뷰"],
        "한옥": ["한옥뷰", "한옥 뷰", "한옥 지붕", "기와지붕"],
        "석촌호수": ["석촌호수", "호수뷰", "호수 뷰"],
        "청계천": ["청계천"],
        "롯데타워": ["롯데타워", "롯데월드타워"],
        "철길": ["철길뷰", "철길 뷰", "기찻길", "철도뷰"],
    }

    VIEW_RE = re.compile(r"([0-9A-Za-z가-힣·]{1,12})\s*뷰")

    def discover(self, evidence_rows: list[dict]) -> list[dict]:
        stats: dict[str, dict] = defaultdict(lambda: {"cafes": set(), "urls": set(), "samples": []})

        for row in evidence_rows:
            if relevance_multiplier(row.get("relevance_score")) <= 0:
                continue
            text = compact_text(row.get("title"), row.get("description"))
            candidates = set()

            for match in self.VIEW_RE.findall(text):
                token = match.strip(" ·-_")
                if token and token not in self.KNOWN and token not in self.STOP and len(token) >= 2:
                    candidates.add(token)

            for canonical, patterns in self.LANDMARK_PATTERNS.items():
                if any(pattern in text for pattern in patterns):
                    candidates.add(canonical)

            for candidate in candidates:
                entry = stats[candidate]
                entry["cafes"].add(row.get("cafe_id", ""))
                if row.get("source_url"):
                    entry["urls"].add(row["source_url"])
                if len(entry["samples"]) < 3:
                    sample = (row.get("title") or row.get("description") or "").strip()
                    if sample:
                        entry["samples"].append(sample[:160])

        rows = []
        for candidate, entry in stats.items():
            rows.append(
                {
                    "view_candidate": candidate,
                    "cafe_count": len({x for x in entry["cafes"] if x}),
                    "evidence_count": len(entry["urls"]),
                    "sample_evidence": " | ".join(entry["samples"]),
                    "suggested_action": "REVIEW_FOR_CATEGORY" if len(entry["cafes"]) >= 2 else "KEEP_AS_TAG",
                }
            )
        return sorted(rows, key=lambda r: (r["cafe_count"], r["evidence_count"], r["view_candidate"]), reverse=True)
