export type Direction = 'UP' | 'DOWN';

export interface Candle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface QuizQuestion {
  questionId: string;
  patternType: string;
  patternName: string;
  patternTip: string;
  difficulty: 'BEGINNER';
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
