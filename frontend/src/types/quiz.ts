export type Direction = 'UP' | 'DOWN';
export type FeatureDirection = 'BULLISH' | 'BEARISH' | 'NEUTRAL';

export interface Candle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartFeatureSignal {
  category: string;
  key: string;
  label: string;
  state: string;
  direction: FeatureDirection;
  strength: number;
  text: string;
  value?: number | string | null;
}

export interface QuizQuestion {
  questionId: string;
  patternType: string;
  patternName: string;
  patternTip: string;
  difficulty: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  features?: ChartFeatureSignal[];
  candles: Candle[];
}

export interface QuizAnswerResult {
  correct: boolean;
  actualAnswer: Direction;
  selectedAnswer: Direction;
  returns: { d1: number; d5: number; d10: number; d20: number };
  explanation: string;
  futureCandles: Candle[];
}
