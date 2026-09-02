import type { Direction } from '../types/quiz';
type Props = { disabled?: boolean; onChoose: (value: Direction) => void };
export function ChoiceButtons({ disabled, onChoose }: Props) {
  return (
    <div className="choice-grid">
      <button disabled={disabled} className="choice-button up" onClick={() => onChoose('UP')}>📈 오른다</button>
      <button disabled={disabled} className="choice-button down" onClick={() => onChoose('DOWN')}>📉 내린다</button>
    </div>
  );
}
