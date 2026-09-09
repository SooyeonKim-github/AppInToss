/**
 * V1 광고 어댑터.
 *
 * 로컬 개발에서는 광고 없이 true를 반환해 재뽑기 흐름을 테스트한다.
 * 앱인토스 광고 콘솔에서 광고 유닛을 발급받은 뒤 이 파일 한 곳에서
 * 공식 Rewarded Ad API를 연결하면 UI/도메인 코드는 수정할 필요가 없다.
 */
export async function showRewardedAd(): Promise<boolean> {
  const adUnitId = import.meta.env.VITE_REWARDED_AD_UNIT_ID;

  if (!adUnitId) {
    return true;
  }

  // 광고 유닛 발급 전에는 SDK 호출을 하드코딩하지 않는다.
  // 운영 연결 시: load -> show -> reward 확인 -> true 반환.
  console.warn("Rewarded ad unit is configured but SDK adapter is not connected yet.");
  return false;
}
