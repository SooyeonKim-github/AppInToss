import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchTodayMenu, fetchTodayRanking, rerollMenu, toggleMenuLike } from "../services/api";
import { showRewardedAd } from "../services/adService";
import type { MenuPickResponse, RankingItem } from "../types";
import { getClientId } from "../utils/clientId";

const REVEAL_DELAY_MS = 1500;

export function useJeomechu() {
  const clientId = useMemo(() => getClientId(), []);
  const [pick, setPick] = useState<MenuPickResponse | null>(null);
  const [ranking, setRanking] = useState<RankingItem[]>([]);
  const [started, setStarted] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [hasRevealedOnce, setHasRevealedOnce] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const revealTimerRef = useRef<number | null>(null);

  const refreshRanking = useCallback(async () => {
    try {
      setRanking(await fetchTodayRanking());
    } catch {
      // 랭킹 실패가 메인 추천 경험을 막지 않게 한다.
    }
  }, []);

  const revealAfterDelay = useCallback(() => {
    if (revealTimerRef.current) window.clearTimeout(revealTimerRef.current);
    revealTimerRef.current = window.setTimeout(() => {
      setRevealed(true);
      setHasRevealedOnce(true);
      setBusy(false);
      revealTimerRef.current = null;
    }, REVEAL_DELAY_MS);
  }, []);

  useEffect(() => {
    let active = true;
    setBusy(true);

    fetchTodayMenu(clientId)
      .then((data) => {
        if (!active) return;
        setPick(data);
        setError(null);
      })
      .catch(() => active && setError("오늘의 메뉴를 불러오지 못했어요."))
      .finally(() => active && setBusy(false));

    refreshRanking();

    return () => {
      active = false;
      if (revealTimerRef.current) window.clearTimeout(revealTimerRef.current);
    };
  }, [clientId, refreshRanking]);

  const startPick = useCallback(() => {
    if (!pick || busy || started) return;
    setStarted(true);
    setRevealed(false);
    setBusy(true);
    revealAfterDelay();
  }, [busy, pick, revealAfterDelay, started]);

  const toggleLike = useCallback(async () => {
    if (!pick || busy) return;
    const result = await toggleMenuLike(clientId, pick.menu.id);
    setPick({ ...pick, liked: result.liked, likes: result.likes });
    await refreshRanking();
  }, [busy, clientId, pick, refreshRanking]);

  const reroll = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    setRevealed(false);

    try {
      const rewarded = await showRewardedAd();
      if (!rewarded) {
        setRevealed(true);
        setBusy(false);
        return;
      }

      const next = await rerollMenu(clientId);
      setPick(next);
      setError(null);
      revealAfterDelay();
    } catch {
      setError("다시 뽑기에 실패했어요. 잠시 후 다시 시도해주세요.");
      setRevealed(true);
      setBusy(false);
    }
  }, [busy, clientId, revealAfterDelay]);

  return {
    pick,
    ranking,
    started,
    revealed,
    hasRevealedOnce,
    busy,
    error,
    startPick,
    toggleLike,
    reroll,
  };
}
