import { ChartCard } from '../components/ChartCard';
import { ChoiceButtons } from '../components/ChoiceButtons';
import type { Direction, QuizQuestion } from '../types/quiz';

type Props = { question: QuizQuestion; index: number; total: number; onAnswer: (v: Direction) => void; loading: boolean };
export function QuizPage({ question, index, total, onAnswer, loading }: Props) {
  return (
    <main className="screen">
      <div className="quiz-header"><span>문제 {index + 1}/{total}</span><span className="badge">입문</span></div>
      <h1 className="quiz-title">이 차트, 오를까?</h1>
      <p className="pattern-label">힌트 · {question.patternName}</p>
      <ChartCard candles={question.candles} />
      <ChoiceButtons disabled={loading} onChoose={onAnswer} />
    </main>
  );
}
