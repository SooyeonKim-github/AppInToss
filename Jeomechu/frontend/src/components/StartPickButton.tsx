interface Props {
  disabled?: boolean;
  onClick: () => void;
}

export function StartPickButton({ disabled, onClick }: Props) {
  return (
    <section className="start-pick">
      <div className="start-pick-icon">🍽️</div>
      <h2>오늘 저녁 뭐 먹지?</h2>
      <p>고민은 김대리에게 맡겨요.</p>
      <button className="start-pick-button" disabled={disabled} onClick={onClick}>
        <span className="start-pick-button-icon">🍴</span>
        <strong>{disabled ? "메뉴 준비 중..." : "오늘 메뉴 뽑기"}</strong>
      </button>
      <small>한 번 누르면 오늘의 메뉴가 공개돼요</small>
    </section>
  );
}
