declare global {
  interface Window {
    kakao?: any;
  }
}

let kakaoPromise: Promise<any> | null = null;

export function loadKakaoMaps(): Promise<any> {
  const key = import.meta.env.VITE_KAKAO_MAP_APP_KEY as string | undefined;
  if (!key) return Promise.reject(new Error("Kakao Maps key is not configured."));
  if (window.kakao?.maps) {
    return new Promise((resolve) => window.kakao.maps.load(() => resolve(window.kakao)));
  }
  if (kakaoPromise) return kakaoPromise;

  kakaoPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${key}&autoload=false`;
    script.async = true;
    script.onload = () => {
      if (!window.kakao?.maps) {
        reject(new Error("Kakao Maps SDK did not load."));
        return;
      }
      window.kakao.maps.load(() => resolve(window.kakao));
    };
    script.onerror = () => reject(new Error("Kakao Maps SDK failed to load."));
    document.head.appendChild(script);
  });

  return kakaoPromise;
}
