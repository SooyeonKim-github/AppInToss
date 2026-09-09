interface Props {
  liked: boolean;
  likes: number;
  disabled?: boolean;
  onClick: () => void;
}

function compact(value: number) {
  return new Intl.NumberFormat("ko-KR", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

export function LikeButton({ liked, likes, disabled, onClick }: Props) {
  return (
    <button className={`like-button ${liked ? "liked" : ""}`} disabled={disabled} onClick={onClick}>
      <span className="heart">{liked ? "❤️" : "♡"}</span>
      <span>{liked ? "오늘 이거 좋다!" : "오늘 이거 좋다"}</span>
      <b>{compact(likes)}</b>
    </button>
  );
}
