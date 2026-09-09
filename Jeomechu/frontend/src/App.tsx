import { DrumRoll } from "./components/DrumRoll";
import { LikeButton } from "./components/LikeButton";
import { MenuRevealCard } from "./components/MenuRevealCard";
import { PopularRanking } from "./components/PopularRanking";
import { useJeomechu } from "./hooks/useJeomechu";

export default function App() {
  const { pick, ranking, revealed, busy, error, toggleLike, reroll } = useJeomechu();

  return (
    <main className="app-shell">
      <header className="brand-header">
        <div className="brand-mark">김대리의 저메추 <span>🍽️</span></div>
        <p>오늘 저녁, 고민은 여기까지.</p>
      </header>

      <section className="hero">
        {!revealed || !pick ? <DrumRoll /> : <MenuRevealCard menu={pick.menu} />}
      </section>

      {error && <p className="error-banner">{error}</p>}

      {pick && revealed && (
        <div className="actions">
          <LikeButton liked={pick.liked} likes={pick.likes} disabled={busy} onClick={toggleLike} />
          <button className="reroll-button" disabled={busy} onClick={reroll}>
            <span>🎲</span>
            <span>다른 거 먹고 싶어요</span>
            <small>광고 보고 다시 뽑기</small>
          </button>
        </div>
      )}

      <PopularRanking items={ranking} />
      <footer>내일은 또 다른 저메추가 찾아와요.</footer>
    </main>
  );
}
