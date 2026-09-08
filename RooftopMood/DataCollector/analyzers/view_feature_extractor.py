from __future__ import annotations

from collections import Counter
import re

from analyzers.evidence_utils import compact_text, relevance_multiplier


class ViewFeatureExtractor:
    """분류 결과와 블로그 Evidence에서 설명 생성에 필요한 최소 feature만 뽑는다.

    방향은 Evidence에 실제 표현이 있을 때만 채운다. 근거가 없으면 UNKNOWN으로 남긴다.
    """

    VIEW_CODES = ("HAN_RIVER", "CITY", "PALACE", "FOREST")

    SUNSET_CUES = ("노을", "일몰", "해질 무렵", "해질무렵", "해지는", "해가 지", "선셋")
    OPENNESS_CUES = ("탁 트", "탁트", "넓게 펼쳐", "한눈에", "파노라마", "시야가 열", "시야가 트")
    FRONT_CUES = ("정면", "바로 앞", "눈앞")
    PARTIAL_CUES = ("건물 사이", "사이로", "부분적으로", "살짝 보")

    LANDMARKS = {
        "남산타워": ("남산타워", "n서울타워", "n 서울타워", "서울타워"),
        "롯데월드타워": ("롯데월드타워", "롯데타워"),
        "경복궁": ("경복궁",),
        "창덕궁": ("창덕궁",),
        "덕수궁": ("덕수궁",),
        "북한산": ("북한산",),
        "서울숲": ("서울숲",),
        "한양도성": ("한양도성", "서울성곽", "성곽"),
    }

    _DIRECTION_PATTERNS = {
        "RIGHT": [
            re.compile(r"(?:오른쪽|오른편|우측).{0,16}(?:노을|일몰|해가|해지는|선셋)"),
            re.compile(r"(?:노을|일몰|해가|해지는|선셋).{0,16}(?:오른쪽|오른편|우측)"),
        ],
        "LEFT": [
            re.compile(r"(?:왼쪽|왼편|좌측).{0,16}(?:노을|일몰|해가|해지는|선셋)"),
            re.compile(r"(?:노을|일몰|해가|해지는|선셋).{0,16}(?:왼쪽|왼편|좌측)"),
        ],
        "FRONT": [
            re.compile(r"(?:정면|앞쪽|바로 앞).{0,16}(?:노을|일몰|해가|해지는|선셋)"),
            re.compile(r"(?:노을|일몰|해가|해지는|선셋).{0,16}(?:정면|앞쪽|바로 앞)"),
        ],
    }

    def extract(self, classification: dict, evidence_rows: list[dict]) -> dict:
        main_view = self._main_view(classification)
        source_urls: set[str] = set()
        sunset_rows = 0
        openness_hits = 0
        front_hits = 0
        partial_hits = 0
        directions: Counter[str] = Counter()
        landmarks: Counter[str] = Counter()

        by_source: dict[str, dict] = {}
        for row in evidence_rows:
            if relevance_multiplier(row.get("relevance_score")) <= 0:
                continue
            key = row.get("source_url") or f"{row.get('title','')}|{row.get('post_date','')}"
            old = by_source.get(key)
            if old is None or int(row.get("relevance_score", 0) or 0) > int(old.get("relevance_score", 0) or 0):
                by_source[key] = row

        for row in by_source.values():
            text = compact_text(row.get("title"), row.get("description"))
            if not text:
                continue
            if row.get("source_url"):
                source_urls.add(row["source_url"])

            if any(cue in text for cue in self.SUNSET_CUES):
                sunset_rows += 1
                for direction, patterns in self._DIRECTION_PATTERNS.items():
                    if any(pattern.search(text) for pattern in patterns):
                        directions[direction] += 1

            if any(cue in text for cue in self.OPENNESS_CUES):
                openness_hits += 1
            if any(cue in text for cue in self.FRONT_CUES):
                front_hits += 1
            if any(cue in text for cue in self.PARTIAL_CUES):
                partial_hits += 1

            for canonical, terms in self.LANDMARKS.items():
                if any(term.lower() in text for term in terms):
                    landmarks[canonical] += 1

        sunset_position = "UNKNOWN"
        sunset_position_confidence = 0.0
        if directions:
            direction, count = directions.most_common(1)[0]
            total_direction_hits = sum(directions.values())
            consistency = count / max(total_direction_hits, 1)
            volume = min(count / 2.0, 1.0)
            sunset_position_confidence = round(0.55 * consistency + 0.45 * volume, 3)
            if sunset_position_confidence >= 0.55:
                sunset_position = direction

        if partial_hits > openness_hits and partial_hits >= 1:
            openness = "PARTIAL"
        elif openness_hits >= 1:
            openness = "OPEN"
        else:
            openness = "UNKNOWN"

        view_position = "FRONT" if front_hits >= 1 else "UNKNOWN"
        landmark_list = [name for name, _ in landmarks.most_common(3)]

        main_score = int(classification.get(f"{main_view.lower()}_score", 0) or 0) if main_view else 0
        main_confidence = float(classification.get(f"{main_view.lower()}_confidence", 0) or 0) if main_view else 0.0

        return {
            "main_view": main_view or "UNKNOWN",
            "main_view_score": main_score,
            "main_view_confidence": round(main_confidence, 3),
            "view_position": view_position,
            "openness": openness,
            "sunset_visible": int(sunset_rows > 0),
            "sunset_evidence_count": sunset_rows,
            "sunset_position": sunset_position,
            "sunset_position_confidence": sunset_position_confidence,
            "landmarks": "|".join(landmark_list),
            "feature_source_count": len(source_urls),
        }

    def _main_view(self, classification: dict) -> str | None:
        candidates: list[tuple[int, float, str]] = []
        for code in self.VIEW_CODES:
            score = int(classification.get(f"{code.lower()}_score", 0) or 0)
            confidence = float(classification.get(f"{code.lower()}_confidence", 0) or 0)
            candidates.append((score, confidence, code))
        score, confidence, code = max(candidates, default=(0, 0.0, ""))
        if score < 2 or confidence < 0.35:
            return None
        return code
