from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

from analyzers.evidence_utils import compact_text, recency_multiplier, relevance_multiplier


class ViewClassifier:
    VIEW_CODES = ("HAN_RIVER", "CITY", "PALACE", "FOREST")

    def __init__(self, config_path: Path, as_of: date | None = None):
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        self.views = payload.get("views", {})
        self.as_of = as_of

    def classify_all(self, candidates: list[dict], evidence_rows: list[dict]) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in evidence_rows:
            grouped[row.get("cafe_id", "")].append(row)
        return [self.classify(cafe, grouped.get(cafe.get("cafe_id", ""), [])) for cafe in candidates]

    def classify(self, cafe: dict, rows: list[dict]) -> dict:
        result = {
            "cafe_id": cafe.get("cafe_id", ""),
            "cafe_name": cafe.get("name", ""),
            "region_code": cafe.get("region_code", ""),
        }
        for code in self.VIEW_CODES:
            stats = self._classify_one(code, rows)
            result.update({f"{code.lower()}_{key}": value for key, value in stats.items()})
        return result

    def _classify_one(self, code: str, rows: list[dict]) -> dict:
        cfg = self.views.get(code, {})
        positive_terms = [x.lower() for x in cfg.get("positive", [])]
        weak_terms = [x.lower() for x in cfg.get("weak_positive", [])]
        negative_terms = [x.lower() for x in cfg.get("negative", [])]

        by_url: dict[str, dict] = {}
        for row in rows:
            key = row.get("source_url") or f"{row.get('title','')}|{row.get('post_date','')}"
            if key not in by_url or int(row.get("relevance_score", 0) or 0) > int(by_url[key].get("relevance_score", 0) or 0):
                by_url[key] = row

        raw_score = 0.0
        positive_rows = 0
        negative_rows = 0
        direct_rows = 0
        source_urls: set[str] = set()
        best_recency = 0.0

        for row in by_url.values():
            rel = relevance_multiplier(row.get("relevance_score"))
            if rel <= 0:
                continue
            text = compact_text(row.get("title"), row.get("description"))
            recency = recency_multiplier(row.get("post_date"), self.as_of)
            best_recency = max(best_recency, recency)

            if any(term in text for term in negative_terms):
                raw_score -= 5.0 * rel * recency
                negative_rows += 1
                if row.get("source_url"):
                    source_urls.add(row["source_url"])
                continue

            if any(term in text for term in positive_terms):
                raw_score += 3.0 * rel * recency
                positive_rows += 1
                direct_rows += 1
                if row.get("source_url"):
                    source_urls.add(row["source_url"])
            elif any(term in text for term in weak_terms):
                raw_score += 1.0 * rel * recency
                positive_rows += 1
                if row.get("source_url"):
                    source_urls.add(row["source_url"])

        source_count = len(source_urls)
        score_5 = self._to_five_point(raw_score, source_count)
        confidence = self._confidence(source_count, positive_rows, negative_rows, direct_rows, best_recency)

        return {
            "score": score_5,
            "raw_score": round(raw_score, 2),
            "confidence": round(confidence, 3),
            "positive_evidence": positive_rows,
            "negative_evidence": negative_rows,
            "source_count": source_count,
        }

    @staticmethod
    def _to_five_point(raw_score: float, source_count: int) -> int:
        if raw_score <= 0:
            score = 0
        elif raw_score < 2.5:
            score = 1
        elif raw_score < 5.0:
            score = 2
        elif raw_score < 8.0:
            score = 3
        elif raw_score < 12.0:
            score = 4
        else:
            score = 5
        if source_count <= 1:
            return min(score, 3)
        if source_count == 2:
            return min(score, 4)
        return score

    @staticmethod
    def _confidence(source_count: int, positive_count: int, negative_count: int, direct_count: int, best_recency: float) -> float:
        volume = min(source_count / 4.0, 1.0)
        direct = 0.0 if positive_count == 0 else min(direct_count / max(positive_count, 1), 1.0)
        total = positive_count + negative_count
        consistency = 0.0 if total == 0 else abs(positive_count - negative_count) / total
        return max(0.0, min(1.0, volume * 0.35 + best_recency * 0.25 + direct * 0.25 + consistency * 0.15))
