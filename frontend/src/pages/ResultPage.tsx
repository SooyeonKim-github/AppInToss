import { ChartCard } from '../components/ChartCard';
import { ReturnProgress } from '../components/ReturnProgress';
import type { QuizAnswerResult } from '../types/quiz';

type Props = { result: QuizAnswerResult; onNext: () => void; isLast: boolean };
export function ResultPage({ result, onNext, isLast }: Props) {
  return (
    <main className="screen">
      <div className={`result-hero ${result.correct ? 'correct' : 'wrong'}`}>
        <div className="result-icon">{result.correct ? '🎉' : '🧐'}</div>
        <h1>{result.correct ? '정답!' : '아쉬워요!'}</h1>
        <p>실제 D+20 결과를 확인해보세요.</p>
      </div>
      <ReturnProgress returns={result.returns} />
      <ChartCard candles={result.futureCandles} showFuture />
      <section className="explanation"><strong>왜 그랬을까?</strong><p>{result.explanation}</p></section>
      <button className="primary-button" onClick={onNext}>{isLast ? '오늘 결과 보기' : '다음 문제'}</button>
    </main>
  );
}
