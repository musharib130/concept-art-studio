type Props = {
  strength: number;
  onStrengthChange: (value: number) => void;
  onReset: () => void;
};

export default function Toolbar({ strength, onStrengthChange, onReset }: Props) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-neutral-800 bg-neutral-950 px-4 py-2">
      <div className="flex items-center gap-2">
        <label htmlFor="strength-slider" className="text-xs text-neutral-400">
          Change amount: {strength.toFixed(2)}
        </label>
        <input
          id="strength-slider"
          type="range"
          min={0.1}
          max={1}
          step={0.05}
          value={strength}
          onChange={(e) => onStrengthChange(Number(e.target.value))}
          className="w-40 accent-blue-500"
        />
      </div>
      <button
        onClick={onReset}
        className="rounded-md border border-neutral-700 px-3 py-1 text-xs text-neutral-300 hover:bg-neutral-800"
      >
        Reset chat
      </button>
    </div>
  );
}
