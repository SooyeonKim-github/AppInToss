from __future__ import annotations

from utils import haversine_m, normalize_address, normalize_name


class CandidateDeduplicator:
    """후보를 canonical cafe 단위로 병합하고 검색 적중 신뢰도를 계산한다."""

    def deduplicate(
        self,
        rows: list[dict],
        region_query_totals: dict[str, int] | None = None,
    ) -> list[dict]:
        clusters: list[list[dict]] = []
        kakao_index: dict[str, int] = {}
        exact_index: dict[tuple[str, str], int] = {}

        for row in rows:
            source = row.get("source", "")
            source_id = row.get("source_place_id", "")
            name_key = normalize_name(row.get("name"))
            addr_key = normalize_address(row.get("road_address") or row.get("address"))

            cluster_idx: int | None = None
            if source == "KAKAO" and source_id and source_id in kakao_index:
                cluster_idx = kakao_index[source_id]
            elif name_key and addr_key and (name_key, addr_key) in exact_index:
                cluster_idx = exact_index[(name_key, addr_key)]
            else:
                cluster_idx = self._find_nearby_match(row, clusters)

            if cluster_idx is None:
                cluster_idx = len(clusters)
                clusters.append([row])
            else:
                clusters[cluster_idx].append(row)

            if source == "KAKAO" and source_id:
                kakao_index[source_id] = cluster_idx
            if name_key and addr_key:
                exact_index[(name_key, addr_key)] = cluster_idx

        totals = region_query_totals or {}
        return [self._merge(cluster, idx + 1, totals) for idx, cluster in enumerate(clusters)]

    @staticmethod
    def _find_nearby_match(row: dict, clusters: list[list[dict]]) -> int | None:
        try:
            lat = float(row.get("latitude"))
            lon = float(row.get("longitude"))
        except (TypeError, ValueError):
            return None

        name_key = normalize_name(row.get("name"))
        if not name_key:
            return None

        for idx, cluster in enumerate(clusters):
            representative = cluster[0]
            if normalize_name(representative.get("name")) != name_key:
                continue
            try:
                other_lat = float(representative.get("latitude"))
                other_lon = float(representative.get("longitude"))
            except (TypeError, ValueError):
                continue
            if haversine_m(lat, lon, other_lat, other_lon) <= 80:
                return idx
        return None

    @staticmethod
    def _merge(cluster: list[dict], cafe_id: int, region_query_totals: dict[str, int]) -> dict:
        representative = next((r for r in cluster if r.get("source") == "KAKAO"), cluster[0])
        providers = sorted({r.get("source", "") for r in cluster if r.get("source")})
        queries = sorted({r.get("search_query", "") for r in cluster if r.get("search_query")})
        regions = [r.get("region_code", "") for r in cluster if r.get("region_code")]
        region_code = max(set(regions), key=regions.count) if regions else ""
        matched_query_count = len(queries)
        region_query_total = int(region_query_totals.get(region_code, matched_query_count or 1))
        query_hit_ratio = matched_query_count / max(region_query_total, 1)

        def first_nonempty(key: str) -> str:
            for candidate in [representative, *cluster]:
                value = candidate.get(key)
                if value not in (None, ""):
                    return str(value)
            return ""

        return {
            "cafe_id": cafe_id,
            "name": first_nonempty("name"),
            "category": first_nonempty("category"),
            "phone": first_nonempty("phone"),
            "address": first_nonempty("address"),
            "road_address": first_nonempty("road_address"),
            "latitude": first_nonempty("latitude"),
            "longitude": first_nonempty("longitude"),
            "region_code": region_code,
            "region_resolution_source": first_nonempty("region_resolution_source"),
            "region_distance_m": first_nonempty("region_distance_m"),
            "region_resolution_confidence": first_nonempty("region_resolution_confidence"),
            "kakao_place_id": next((r.get("source_place_id", "") for r in cluster if r.get("source") == "KAKAO"), ""),
            "kakao_url": next((r.get("source_url", "") for r in cluster if r.get("source") == "KAKAO"), ""),
            "naver_url": next((r.get("source_url", "") for r in cluster if r.get("source") == "NAVER"), ""),
            "providers": "|".join(providers),
            "matched_queries": "|".join(queries),
            "matched_query_count": matched_query_count,
            "region_query_total": region_query_total,
            "query_hit_ratio": round(query_hit_ratio, 3),
            "raw_match_count": len(cluster),
        }
