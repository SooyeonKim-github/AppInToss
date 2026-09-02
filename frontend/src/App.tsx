import { useEffect, useMemo, useState } from 'react';
import './styles.css';
import { HomePage } from './pages/HomePage';
import { PatternCard } from './components/PatternCard';
import { QuizPage } from './pages/QuizPage';
import { ResultPage } from './pages/ResultPage';
import { DailyResultPage } from './pages/DailyResultPage';
import { quizApi } from './services/quizApi';
import { statsApi } from './services/statsApi';
import type { Direction, QuizAnswerResult, QuizQuestion } from './types/quiz';
import type { UserStats } from './types/stats';

const USER_ID_KEY = 'oreulkka-user-id';
function getUserId() {
  const found = localStorage.getItem(USER_ID_KEY);
  if (found) return found;
  const value = crypto.randomUUID();
  localStorage.setItem(USER_ID_KEY, value);
  return value;
}

type Stage = 'home' | 'intro' | 'quiz' | 'result' | 'daily';

export default function App() {
  const userId = useMemo(getUserId, []);
  const [stage, setStage] = useState<Stage>('home');
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<QuizAnswerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [score, setScore] = useState(0);
  const [stats, setStats] = useState<UserStats | null>(null);

  const refreshStats = async () => {
    try { setStats(await statsApi.get(userId)); } catch { setStats(null); }
  };
  useEffect(() => { void refreshStats(); }, []);

  const start = async () => {
    setLoading(true);
    try {
      const items = await quizApi.today(5);
      setQuestions(items);
      setIndex(0);
      setScore(0);
      setStage(items.length ? 'intro' : 'home');
    } finally { setLoading(false); }
  };

  const answer = async (direction: Direction) => {
    const q = questions[index];
    if (!q) return;
    setLoading(true);
    try {
      const value = await quizApi.answer(q.questionId, direction, userId);
      setResult(value);
      if (value.correct) setScore((x) => x + 1);
      setStage('result');
    } finally { setLoading(false); }
  };

  const next = async () => {
    if (index + 1 >= questions.length) {
      await refreshStats();
      setStage('daily');
      return;
    }
    setIndex((x) => x + 1);
    setResult(null);
    setStage('quiz');
  };

  const current = questions[index];
  if (stage === 'home') return <HomePage stats={stats} onStart={start} />;
  if (stage === 'intro' && current) return <main className="screen"><PatternCard name={current.patternName} tip={current.patternTip} onStart={() => setStage('quiz')} /></main>;
  if (stage === 'quiz' && current) return <QuizPage question={current} index={index} total={questions.length} onAnswer={answer} loading={loading} />;
  if (stage === 'result' && result) return <ResultPage result={result} isLast={index + 1 >= questions.length} onNext={next} />;
  if (stage === 'daily') return <DailyResultPage score={score} total={questions.length} stats={stats} onHome={() => setStage('home')} />;
  return <main className="screen"><p>{loading ? '불러오는 중...' : '문제를 불러오지 못했어요.'}</p><button className="primary-button" onClick={() => setStage('home')}>홈으로</button></main>;
}
