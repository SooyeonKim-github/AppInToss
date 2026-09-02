import { api } from './api';
import type { Direction, QuizAnswerResult, QuizQuestion } from '../types/quiz';

export const quizApi = {
  today: (limit = 5) => api<QuizQuestion[]>(`/api/quiz/today?limit=${limit}`),
  answer: (questionId: string, answer: Direction, userId: string) =>
    api<QuizAnswerResult>(`/api/quiz/${questionId}/answer`, {
      method: 'POST',
      body: JSON.stringify({ answer, userId }),
    }),
};
