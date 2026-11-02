import { STEPS, type StepId } from "../route";

export default function StepNav({ current, onChange }: { current: StepId; onChange: (s: StepId) => void }) {
  return (
    <nav aria-label="CRISP-DM 步驟">
      <ol className="steps">
        {STEPS.map((s, i) => (
          <li key={s.id}>
            <button type="button" aria-current={current === s.id ? "step" : undefined} onClick={() => onChange(s.id)}>
              <span className="num">{"①②③④⑤⑥"[i]}</span>
              <span className="zh">{s.label}</span>
              <span className="en">{s.en}</span>
            </button>
          </li>
        ))}
      </ol>
    </nav>
  );
}
