export interface PatternStat {
  patternType: string;
  patternName: string;
  attempts: number;
  accuracy: number;
  avgD20ReturnOnUp: number;
}

export interface UserStats {
  totalAttempts: number;
  correctCount: number;
  accuracy: number;
  upPredictions: number;
  upAccuracy: number;
  avgReturnD1: number;
  avgReturnD5: number;
  avgReturnD10: number;
  avgReturnD20: number;
  patternStats: PatternStat[];
}
