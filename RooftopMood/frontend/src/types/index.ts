export type ViewCode = "HAN_RIVER" | "CITY" | "PALACE" | "FOREST";

export type ViewOption = {
  code: ViewCode;
  name: string;
  emoji: string;
};

export type Region = {
  code: string;
  name: string;
  cafeCount: number;
};

export type SunsetInfo = {
  date: string;
  time: string;
  score: number;
  message: string;
  weather: {
    cloudCover: number;
    precipitationProbability: number;
    visibilityKm: number;
    source: string;
    forecastTime?: string | null;
  };
};

export type HomeResponse = {
  app: {
    name: string;
    description: string;
  };
  sunset: SunsetInfo;
  views: ViewOption[];
};

export type TodaySunsetInfo = {
  date: string;
  sunsetTime: string;
  sunsetAzimuthDeg: number;
  viewDirectionDeg?: number | null;
  position: "FRONT" | "RIGHT" | "LEFT" | "OUT_OF_VIEW" | "UNKNOWN";
  positionLabel: string;
  alignmentScore: number;
  visible: boolean;
  bestTime: string;
  message: string;
  confidence: number;
};

export type PhotoStatus = "PENDING" | "APPROVED";

export type Recommendation = {
  id: number;
  name: string;
  regionName: string;
  address: string;
  viewDescription: string;
  bestSeatTip: string;
  todaySunsetInfo: TodaySunsetInfo;
  score: number;
  tags: string[];
  imageUrl?: string | null;
  photoStatus?: PhotoStatus | null;
  canUploadPhoto?: boolean;
  kakaoMapUrl?: string | null;
};

export type PhotoUploadResponse = {
  cafeId: number;
  imageUrl?: string | null;
  status: "PENDING";
  message: string;
};
