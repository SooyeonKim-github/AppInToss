interface Props {
  liked: boolean;
  disabled?: boolean;
  onClick: () => void;
}

export function LikeButton({ liked, disabled, onClick }: Props) {
  return (
    <button className={`like-button ${liked ? "liked" : ""}`} disabled={disabled} onClick={onClick}>
      <span className="action-main">
        <span className="action-icon heart">{liked ? "❤️" : "♡"}</span>
        <span>좋아요</span>
      </span>
      <small className="action-sub">오늘은 이거다</small>
    </button>
  );
}
