import { loadFullScreenAd, showFullScreenAd } from "@apps-in-toss/web-framework";

const REWARDED_AD_GROUP_ID = import.meta.env.VITE_REWARDED_AD_UNIT_ID?.trim() ?? "";
const LOAD_TIMEOUT_MS = 10_000;
const SHOW_TIMEOUT_MS = 120_000;
const REWARD_DISMISS_FALLBACK_MS = 1_500;

let adLoaded = false;
let loadPromise: Promise<boolean> | null = null;
let loadCleanup: (() => void) | null = null;

function isLocalDevelopment() {
  return import.meta.env.DEV;
}

function isRewardedAdSupported() {
  if (!REWARDED_AD_GROUP_ID) return false;

  try {
    return loadFullScreenAd.isSupported() && showFullScreenAd.isSupported();
  } catch {
    return false;
  }
}

/**
 * 화면 진입 시 광고를 미리 불러둔다.
 * 공식 권장 흐름인 load -> loaded -> show 순서를 보장한다.
 */
export function preloadRewardedAd(): Promise<boolean> {
  // 일반 브라우저 로컬 개발에서는 광고 없이 전체 UX를 테스트한다.
  if (isLocalDevelopment()) return Promise.resolve(true);

  if (!REWARDED_AD_GROUP_ID) {
    console.warn("VITE_REWARDED_AD_UNIT_ID is not configured.");
    return Promise.resolve(false);
  }

  if (!isRewardedAdSupported()) {
    console.warn("Rewarded ads are not supported in this Apps-in-Toss environment.");
    return Promise.resolve(false);
  }

  if (adLoaded) return Promise.resolve(true);
  if (loadPromise) return loadPromise;

  loadPromise = new Promise<boolean>((resolve) => {
    let settled = false;

    const finish = (loaded: boolean) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timeoutId);
      loadCleanup?.();
      loadCleanup = null;
      adLoaded = loaded;
      loadPromise = null;
      resolve(loaded);
    };

    const timeoutId = window.setTimeout(() => {
      console.warn("Rewarded ad preload timed out.");
      finish(false);
    }, LOAD_TIMEOUT_MS);

    try {
      loadCleanup = loadFullScreenAd({
        options: { adGroupId: REWARDED_AD_GROUP_ID },
        onEvent: (event) => {
          if (event.type === "loaded") finish(true);
        },
        onError: (error) => {
          console.error("Rewarded ad preload failed.", error);
          finish(false);
        },
      });
    } catch (error) {
      console.error("Rewarded ad preload threw an error.", error);
      finish(false);
    }
  });

  return loadPromise;
}

function preloadNextRewardedAd() {
  window.setTimeout(() => {
    void preloadRewardedAd();
  }, 300);
}

/**
 * 보상형 광고를 보여주고 실제 보상 획득 여부만 반환한다.
 * dismissed/clicked가 아니라 userEarnedReward 이벤트가 발생해야 true가 된다.
 */
export async function showRewardedAd(): Promise<boolean> {
  if (isLocalDevelopment()) return true;

  if (!REWARDED_AD_GROUP_ID || !isRewardedAdSupported()) return false;

  const ready = await preloadRewardedAd();
  if (!ready) return false;

  // 한 번 표시한 광고는 재사용할 수 없으므로 즉시 loaded 상태를 소진한다.
  adLoaded = false;

  return new Promise<boolean>((resolve) => {
    let promiseResolved = false;
    let rewardEarned = false;
    let showCleanup: (() => void) | null = null;
    let rewardFallbackId: number | null = null;

    const resolveOnce = (value: boolean) => {
      if (promiseResolved) return;
      promiseResolved = true;
      resolve(value);
    };

    const cleanup = () => {
      window.clearTimeout(showTimeoutId);
      if (rewardFallbackId !== null) window.clearTimeout(rewardFallbackId);
      showCleanup?.();
      showCleanup = null;
    };

    const finishAdSession = (rewarded: boolean) => {
      resolveOnce(rewarded);
      cleanup();
      preloadNextRewardedAd();
    };

    const showTimeoutId = window.setTimeout(() => {
      console.warn("Rewarded ad show timed out.");
      finishAdSession(false);
    }, SHOW_TIMEOUT_MS);

    try {
      showCleanup = showFullScreenAd({
        options: { adGroupId: REWARDED_AD_GROUP_ID },
        onEvent: (event) => {
          switch (event.type) {
            case "userEarnedReward":
              rewardEarned = true;

              // 일부 토스 앱 버전에서 dismissed 이벤트가 누락될 수 있어
              // 보상 이벤트 자체를 최종 안전장치로 사용한다.
              rewardFallbackId = window.setTimeout(() => {
                resolveOnce(true);
              }, REWARD_DISMISS_FALLBACK_MS);
              break;

            case "dismissed":
              finishAdSession(rewardEarned);
              break;

            case "failedToShow":
              console.warn("Rewarded ad failed to show.");
              finishAdSession(false);
              break;
          }
        },
        onError: (error) => {
          console.error("Rewarded ad show failed.", error);
          finishAdSession(false);
        },
      });
    } catch (error) {
      console.error("Rewarded ad show threw an error.", error);
      finishAdSession(false);
    }
  });
}
