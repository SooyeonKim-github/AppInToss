from __future__ import annotations


class TemplateDescriptionGenerator:
    """외부 LLM 없이 DB 저장용 '고정' 뷰 설명을 생성한다.

    일몰 시각/방향은 날짜에 따라 변하므로 이 문장에는 절대 넣지 않는다.
    앱에서는 백엔드의 todaySunsetInfo를 별도로 표시한다.
    """

    GENERATOR_VERSION = "RULE_VIEW_ONLY_V2"

    OPEN_FRONT = {
        "HAN_RIVER": "한강이 정면으로 넓게 펼쳐지는 탁 트인 루프탑이에요.",
        "CITY": "서울 도심이 정면으로 시원하게 펼쳐지는 루프탑이에요.",
        "PALACE": "궁궐과 한옥 지붕이 정면으로 펼쳐지는 루프탑이에요.",
        "FOREST": "푸른 숲이 정면으로 넓게 펼쳐지는 루프탑이에요.",
    }
    OPEN = {
        "HAN_RIVER": "한강이 넓게 펼쳐지는 탁 트인 루프탑이에요.",
        "CITY": "서울 도심이 시원하게 내려다보이는 루프탑이에요.",
        "PALACE": "궁궐과 한옥 풍경이 넓게 내려다보이는 루프탑이에요.",
        "FOREST": "도심 속 푸른 숲이 넓게 펼쳐지는 루프탑이에요.",
    }
    PARTIAL = {
        "HAN_RIVER": "건물 사이로 한강 풍경이 보이는 루프탑이에요.",
        "CITY": "주변 건물 너머로 서울 도심이 보이는 루프탑이에요.",
        "PALACE": "건물 사이로 궁궐과 한옥 풍경이 보이는 루프탑이에요.",
        "FOREST": "주변 건물 사이로 푸른 숲이 보이는 루프탑이에요.",
    }
    DEFAULT = {
        "HAN_RIVER": "루프탑에서 한강 풍경을 즐길 수 있어요.",
        "CITY": "루프탑에서 서울 도심 풍경을 즐길 수 있어요.",
        "PALACE": "루프탑에서 궁궐과 한옥 풍경을 즐길 수 있어요.",
        "FOREST": "루프탑에서 도심 속 초록 풍경을 즐길 수 있어요.",
    }

    def generate(self, features: dict, rooftop_status: str = "") -> dict:
        main_view = features.get("main_view", "UNKNOWN")
        score = int(features.get("main_view_score", 0) or 0)
        main_conf = float(features.get("main_view_confidence", 0) or 0)

        if rooftop_status not in {"CONFIRMED", "PROBABLE"} or main_view not in self.DEFAULT or score < 2:
            return self._empty("INSUFFICIENT_EVIDENCE")

        openness = features.get("openness", "UNKNOWN")
        view_position = features.get("view_position", "UNKNOWN")
        if openness == "PARTIAL":
            description = self.PARTIAL[main_view]
        elif openness == "OPEN" and view_position == "FRONT":
            description = self.OPEN_FRONT[main_view]
        elif openness == "OPEN":
            description = self.OPEN[main_view]
        else:
            description = self.DEFAULT[main_view]

        confidence = self._confidence(main_conf, openness, view_position)
        review_required = confidence < 0.62
        return {
            "view_description": description,
            "description_length": len(description),
            "description_confidence": round(confidence, 3),
            "description_generated_by": self.GENERATOR_VERSION,
            "description_review_required": int(review_required),
            "description_reason": "LOW_CONFIDENCE" if review_required else "AUTO_READY",
        }

    @staticmethod
    def _confidence(main_conf: float, openness: str, view_position: str) -> float:
        openness_component = 0.78 if openness != "UNKNOWN" else 0.5
        position_component = 0.75 if view_position == "FRONT" else 0.58
        return max(0.0, min(1.0, main_conf * 0.72 + openness_component * 0.18 + position_component * 0.10))

    @staticmethod
    def _empty(reason: str) -> dict:
        return {
            "view_description": "",
            "description_length": 0,
            "description_confidence": 0.0,
            "description_generated_by": TemplateDescriptionGenerator.GENERATOR_VERSION,
            "description_review_required": 1,
            "description_reason": reason,
        }
