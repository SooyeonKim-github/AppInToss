export type SpotCategory = "cafe" | "park" | "bridge" | "commute" | "walk";

export type SunsetSpot = {
  id: string; name: string; typeLabel: string; categories: SpotCategory[];
  latitude: number; longitude: number; viewDirectionDeg: number;
  station: string; walkMinutes: number; viewLabel: string; guide: string;
  address: string; baseScore: number; theme: "city" | "river" | "park";
  verification: "candidate" | "verified";
};

export const sunsetSpots: SunsetSpot[] = [
  { id:"hangang-overpass", name:"한강초교 앞 보행육교", typeLabel:"🌉 육교", categories:["bridge","commute"], latitude:37.5246, longitude:126.9707, viewDirectionDeg:272, station:"한강진역", walkMinutes:7, viewLabel:"건물 사이 노을", guide:"육교 서쪽 끝 난간에서 건물 사이로 내려오는 해를 정면으로 볼 수 있어요.", address:"서울 용산구 한남동 707-1 인근", baseScore:82, theme:"city", verification:"candidate" },
  { id:"nodeul-west", name:"노들섬 서측 산책로", typeLabel:"🌿 공원", categories:["park","walk"], latitude:37.5172, longitude:126.9586, viewDirectionDeg:268, station:"노들역", walkMinutes:12, viewLabel:"잔디밭 너머 노을", guide:"서측 강변 산책로에서 한강 너머로 천천히 낮아지는 해를 넓게 볼 수 있어요.", address:"서울 용산구 양녕로 445", baseScore:91, theme:"park", verification:"candidate" },
  { id:"jamsu-west", name:"잠수교 중앙 서쪽 보행구간", typeLabel:"🌉 보행교", categories:["bridge","walk"], latitude:37.5133, longitude:127.0051, viewDirectionDeg:267, station:"고속터미널역", walkMinutes:15, viewLabel:"한강 정면 노을", guide:"낮은 다리 위에서 물결과 같은 눈높이로 한강 정면의 노을을 만날 수 있어요.", address:"서울 서초구 반포동 649", baseScore:88, theme:"river", verification:"candidate" },
  { id:"mangwon-river", name:"망원한강공원", typeLabel:"🌊 한강공원", categories:["park","walk","commute"], latitude:37.55237, longitude:126.89986, viewDirectionDeg:274, station:"망원역", walkMinutes:19, viewLabel:"물 위로 번지는 노을", guide:"강변을 걷다 보면 성산대교 옆으로 붉게 내려앉는 노을이 보여요.", address:"서울 마포구 마포나루길 467", baseScore:89, theme:"river", verification:"verified" },
  { id:"chaegeuro", name:"채그로 루프탑", typeLabel:"☕ 카페", categories:["cafe"], latitude:37.5362, longitude:126.9436, viewDirectionDeg:270, station:"마포역", walkMinutes:8, viewLabel:"통창 너머 한강 노을", guide:"높은 통창과 루프탑에서 한강 뒤로 번지는 주황빛 노을을 편하게 감상할 수 있어요.", address:"서울 마포구 마포대로4다길 31", baseScore:84, theme:"river", verification:"candidate" },
  { id:"eungbong", name:"응봉산 팔각정", typeLabel:"⛰️ 전망대", categories:["park","walk"], latitude:37.5484, longitude:127.0301, viewDirectionDeg:260, station:"응봉역", walkMinutes:14, viewLabel:"서울숲 너머 노을", guide:"낮은 산책길 끝 전망대에서 서울숲과 한강 너머의 노을을 한눈에 볼 수 있어요.", address:"서울 성동구 금호동4가 1540", baseScore:87, theme:"park", verification:"verified" }
];
