interface AgentToggleProps {
  enabled: boolean;
  onChange: (next: boolean) => void;
}

export function AgentToggle({ enabled, onChange }: AgentToggleProps) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      className={`group flex items-center gap-3 rounded-full border px-4 py-2 text-sm font-semibold shadow transition ${
        enabled
          ? "border-brand-500 bg-brand-50 text-brand-700"
          : "border-slate-200 bg-white text-slate-600"
      }`}
    >
      <span>Agent {enabled ? "ON" : "OFF"}</span>
      <span
        className={`relative inline-flex h-6 w-12 items-center rounded-full transition ${
          enabled ? "bg-brand-500" : "bg-slate-300"
        }`}
      >
        <span
          className={`inline-block h-5 w-5 rounded-full bg-white shadow transition ${
            enabled ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </span>
    </button>
  );
}

export default AgentToggle;






