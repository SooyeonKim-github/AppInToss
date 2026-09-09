import { DrumRoll } from "./components/DrumRoll";
import { LikeButton } from "./components/LikeButton";
import { MenuRevealCard } from "./components/MenuRevealCard";
import { PopularRanking } from "./components/PopularRanking";
import { useJeomechu } from "./hooks/useJeomechu";

export default function App() {
  const {
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
  } = useJeomechu();

  const handleReroll = () => {
    if (!started) {
      startPick();
      return;
    }
    reroll();
  };

  return (
    <main className="app-shell">
      <header className="brand-header">
        <div className="brand-mark">김대리의 저메추 <span>🍽️</span></div>
        <p>오늘 저녁, 고민은 여기까지.</p>
      </header>

      <section className="hero">
        {!started ? (
          <button
            className="start-pick"
            disabled={!pick || busy}
            onClick={startPick}
            aria-label="오늘 저녁메뉴 뽑기"
          >
            <span className="start-pick-icon" aria-hidden="true">🍽️</span>
            <span className="start-pick-title">오늘 저녁메뉴 뽑기</span>
          </button>
        ) : !revealed || !pick ? (
          <DrumRoll />
        ) : (
          <MenuRevealCard menu={pick.menu} />
        )}
      </section>

      {error && <p className="error-banner">{error}</p>}

      <div className="actions">
        <LikeButton
          liked={pick?.liked ?? false}
          disabled={!pick || !hasRevealedOnce || busy}
          onClick={toggleLike}
        />
        <button className="reroll-button" disabled={!pick || busy} onClick={handleReroll}>
          <span className="action-main"><span className="action-icon">🎲</span><span>다시뽑기</span></span>
          <small className="action-sub">한 번 더 골라요</small>
        </button>
      </div>

      <PopularRanking items={ranking} />
      <footer>내일은 또 다른 저메추가 찾아와요.</footer>
    </main>
  );
}
