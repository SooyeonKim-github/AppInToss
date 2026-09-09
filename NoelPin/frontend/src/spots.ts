export type SunsetSpot = {
  id: string;
  name: string;
  shortName: string;
  latitude: number;
  longitude: number;
  walkMinutes: number;
  tags: string[];
  guide: string;
  viewDirection: string;
  arrivalTip: string;
  transit?: {
    line: string;
    section: string;
    windowSide: string;
  };
  verification: "candidate" | "verified";
};

export const sunsetSpots: SunsetSpot[] = [
  {
    id: "hangang-elementary-overpass",
    name: "한강초교 앞 보행육교",
    shortName: "한강초교 앞 육교",
    latitude: 37.5246,
    longitude: 126.9707,
    walkMinutes: 7,
    tags: ["육교위노을", "건물사이노을", "퇴근길노을"],
    guide: "육교 중앙보다 서쪽 끝 난간 쪽에서 시야가 더 열리는 후보예요.",
    viewDirection: "서쪽 끝 난간에서 서쪽 하늘",
    arrivalTip: "일몰 20~30분 전에 도착해 주변 보행 동선을 먼저 확인해 주세요.",
    verification: "candidate",
  },
  {
    id: "jamsu-bridge-west",
    name: "잠수교 중앙 서쪽 보행구간",
    shortName: "잠수교 중앙",
    latitude: 37.5133,
    longitude: 127.0051,
    walkMinutes: 12,
    tags: ["다리위노을", "한강노을", "산책노을"],
    guide: "잠수교 중앙부에서 서쪽 한강 쪽으로 시야가 열리는 보행 구간 후보예요.",
    viewDirection: "서쪽 한강 방향",
    arrivalTip: "강바람이 강할 수 있어 일몰 전 여유 있게 이동하는 편이 좋아요.",
    verification: "candidate",
  },
  {
    id: "nodeul-west-walk",
    name: "노들섬 서측 산책로",
    shortName: "노들섬 서측",
    latitude: 37.5172,
    longitude: 126.9586,
    walkMinutes: 15,
    tags: ["산책노을", "한강노을"],
    guide: "서측 강변 산책로에서 한강 너머로 노을을 보기 좋은 후보 구간이에요.",
    viewDirection: "서쪽 강변",
    arrivalTip: "일몰 30분 전부터 하늘색이 바뀌는 구간을 천천히 걸어보세요.",
    verification: "candidate",
  },
  {
    id: "subway-hangang-window",
    name: "지하철 한강 통과 창밖노을",
    shortName: "지하철 창밖노을",
    latitude: 37.5205,
    longitude: 126.9635,
    walkMinutes: 0,
    tags: ["지하철창밖노을", "퇴근길노을"],
    guide: "지하철이 한강을 지나는 짧은 순간, 열린 창밖으로 노을을 보는 타입이에요.",
    viewDirection: "탑승 방향에 따라 창문 방향 확인",
    arrivalTip: "실제 노선·방향·창문 위치 데이터는 현장 검증 후 확정할 예정이에요.",
    transit: {
      line: "지상 한강 통과 노선",
      section: "한강 통과 구간",
      windowSide: "진행 방향에 따라 안내 예정",
    },
    verification: "candidate",
  },
];
