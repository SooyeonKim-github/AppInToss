import { api } from './api';
import type { UserStats } from '../types/stats';

export const statsApi = {
  get: (userId: string) => api<UserStats>(`/api/stats/${encodeURIComponent(userId)}`),
};
