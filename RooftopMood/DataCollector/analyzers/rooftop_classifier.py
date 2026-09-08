from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

from analyzers.evidence_utils import compact_text, count_distinct_sources, recency_multiplier, relevance_multiplier


class RooftopClassifier:
    def __init__(self, config_path: Path, as_of: date | None = None):
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        self.strong = [x.lower() for x in payload.get("positive_strong", [])]
        self.medium = [x.lower() for x in payload.get("positive_medium", [])]
        self.negative = [x.lower() for x in payload.get("negative_strong", [])]
        self.as_of = as_of

    def classify_all(self, candidates: list[dict], evidence_rows: list[dict]) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in evidence_rows:
            grouped[row.get("cafe_id", "")].append(row)
        return [self.classify(cafe, grouped.get(cafe.get("cafe_id", ""), [])) for cafe in candidates]

    def classify(self, cafe: dict, rows: list[dict]) -> dict:
        weighted_score = 0.0
        positive_rows: list[dict] = []
        negative_rows: list[dict] = []
        direct_strength_total = 0.0
        recent_negative = False

        by_url: dict[str, dict] = {}
        for row in rows:
            key = row.get("source_url") or f"{row.get('title','')}|{row.get('post_date','')}"
            if key not in by_url or int(row.get("relevance_score", 0) or 0) > int(by_url[key].get("relevance_score", 0) or 0):
                by_url[key] = row

        for row in by_url.values():
            rel = relevance_multiplier(row.get("relevance_score"))
            if rel <= 0:
                continue
            recency = recency_multiplier(row.get("post_date"), self.as_of)
            text = compact_text(row.get("title"), row.get("description"))

            negative_hits = [kw for kw in self.negative if kw in text]
            strong_hits = [kw for kw in self.strong if kw in text]
            medium_hits = [kw for kw in self.medium if kw in text]

            if negative_hits:
                contribution = -8.0 * rel * recency
                weighted_score += contribution
                negative_rows.append(row)
                direct_strength_total += 1.0
                if recency >= 0.8:
                    recent_negative = True
                continue

            contribution = 0.0
            if strong_hits:
                contribution += 4.0
                direct_strength_total += 1.0
            if medium_hits:
                contribution += 1.5
                direct_strength_total += 0.5
            if contribution > 0:
                weighted_score += contribution * rel * recency
                positive_rows.append(row)

        source_count = count_distinct_sources(positive_rows + negative_rows)
        positive_count = len(positive_rows)
        negative_count = len(negative_rows)

        if recent_negative and negative_count >= positive_count:
            status = "REJECT"
        elif weighted_score >= 9:
            status = "CONFIRMED"
        elif weighted_score >= 4:
            status = "PROBABLE"
        elif weighted_score > 0:
            status = "REVIEW"
        else:
            status = "REJECT"

        confidence = self._confidence(source_count=source_count, positive_count=positive_count, negative_count=negative_count, direct_strength=direct_strength_total)

        return {
            "cafe_id": cafe.get("cafe_id", ""),
            "cafe_name": cafe.get("name", ""),
            "region_code": cafe.get("region_code", ""),
            "rooftop_status": status,
            "rooftop_score": round(weighted_score, 2),
            "rooftop_confidence": round(confidence, 3),
            "rooftop_positive_evidence": positive_count,
            "rooftop_negative_evidence": negative_count,
            "rooftop_source_count": source_count,
            "rooftop_recent_negative": int(recent_negative),
        }

    @staticmethod
    def _confidence(source_count: int, positive_count: int, negative_count: int, direct_strength: float) -> float:
        source_score = min(source_count / 4.0, 1.0)
        direct_score = min(direct_strength / 4.0, 1.0)
        total = positive_count + negative_count
        consistency = 0.0 if total == 0 else abs(positive_count - negative_count) / total
        evidence_volume = min(total / 5.0, 1.0)
        return max(0.0, min(1.0, source_score * 0.35 + direct_score * 0.25 + consistency * 0.2 + evidence_volume * 0.2))
