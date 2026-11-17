import React, { useEffect, useRef, useState } from 'react';
import { FileText, RefreshCw, AlertTriangle, CheckCircle2, Wand2, RotateCcw } from 'lucide-react';
import { apiService } from '../../services/apiService';

/**
 * Design Script panel
 * -------------------
 * Shows the ArchiScript that Gemini wrote for this design. The user can
 *  - edit it and press "Run script" (the CAD engine runs and tests it, no AI call), or
 *  - ask for a change in plain words; Gemini edits the script and the engine tests it again.
 * Problems the engine finds are listed by script line number.
 */

interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
}

interface DesignScriptPanelProps {
  design: any;
  onDesign: (design: any) => void;
  fallbackPrompt?: string;
}

export const DesignScriptPanel: React.FC<DesignScriptPanelProps> = ({ design, onDesign, fallbackPrompt }) => {
  const [script, setScript] = useState<string>(design?.design_script || '');
  const [aiScript, setAiScript] = useState<string>(design?.design_script || '');
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState<'run' | 'chat' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const lastProject = useRef<string | null>(null);

  // A new design from the server replaces the editor content (keeps the conversation)
  useEffect(() => {
    if (design?.design_script && design?.project_id !== lastProject.current) {
      lastProject.current = design.project_id;
      setScript(design.design_script);
      if (design.design_source !== 'client_edited_script') setAiScript(design.design_script);
    }
  }, [design?.project_id, design?.design_script, design?.design_source]);

  if (!design?.design_script) return null;

  const basePayload = () => ({
    script,
    prompt: design?.brief || fallbackPrompt || '',
    plot_width: design?.plot?.width_ft ?? design?.layout_json?.plot_width_ft ?? 35,
    plot_length: design?.plot?.length_ft ?? design?.layout_json?.plot_length_ft ?? 65,
    floors: design?.floors ?? 1,
    bedrooms: design?.requirements?.parsed?.bedrooms ?? 3,
    bathrooms: design?.requirements?.parsed?.bathrooms ?? 3,
    style: design?.style || 'modern contemporary',
    requirements: design?.requirements?.parsed,
  });

  const runScript = async () => {
    setBusy('run');
    setError(null);
    try {
      const res = await apiService.runDesignScript(basePayload());
      onDesign(res);
    } catch (e: any) {
      setError(e?.message || 'Running the script failed');
    } finally {
      setBusy(null);
    }
  };

  const sendMessage = async () => {
    const text = message.trim();
    if (!text) return;
    const history = [...chat];
    setChat([...history, { role: 'user', text }]);
    setMessage('');
    setBusy('chat');
    setError(null);
    try {
      const res = await apiService.converseDesignScript({ ...basePayload(), message: text, history });
      setChat((c) => [...c, { role: 'assistant', text: res.assistant_message || 'Updated the script.' }]);
      onDesign(res);
    } catch (e: any) {
      setChat((c) => [...c, { role: 'assistant', text: `Sorry - ${e?.message || 'the change failed'}` }]);
    } finally {
      setBusy(null);
    }
  };

  const status = design?.quality_gate?.status;
  const problems: string[] = design?.script_problems || [];
  const rounds: any[] = design?.script_rounds || [];
  const edited = script !== design.design_script;

  return (
    <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-3">
      <div className="flex items-center justify-between border-b border-[#E2E7E1] pb-2.5 gap-2">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-[#23483D]" />
          <h3 className="font-bold text-xs text-[#202923] uppercase tracking-wider">Design Script (ArchiScript)</h3>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
          status === 'PASS'
            ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
            : 'bg-amber-100 text-amber-800 border-amber-300'
        }`}>
          {status === 'PASS' ? 'Engine checks passed' : `${problems.length} problem(s) to fix`}
        </span>
      </div>

      {design?.requirements?.understood_as && (
        <p className="text-[11px] text-[#202923]">
          <span className="font-bold text-[#23483D]">Understood from your prompt: </span>
          {design.requirements.understood_as}
        </p>
      )}

      {rounds.length > 0 && (
        <p className="text-[10px] text-[#68736C]">
          {rounds.map((r) => `${r.source === 'gemini' ? (r.level != null ? `Level ${r.level}, AI round` : 'AI round') : r.source === 'conversation' ? 'Change round' : 'Your run'} ${r.round || ''}: ${r.errors} problem(s)`).join('  →  ')}
        </p>
      )}

      <textarea
        value={script}
        onChange={(e) => setScript(e.target.value)}
        spellCheck={false}
        rows={16}
        className="w-full font-mono text-[11px] leading-[1.45] p-3 rounded-xl border border-[#E2E7E1] bg-[#FAFBF9] text-[#202923] focus:outline-none focus:ring-2 focus:ring-[#23483D]/30 whitespace-pre overflow-auto"
      />
      <p className="text-[10px] text-[#8C9890]">
        One line per space: <span className="font-mono">size | NAME | type | door: NAME | furniture: …</span>. ROWS run front → back,
        COLS left → right; sizes in feet. Press Run to redraw and re-check.
      </p>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={runScript}
          disabled={busy !== null}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#23483D] text-white text-xs font-bold disabled:opacity-50"
        >
          {busy === 'run' ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
          {busy === 'run' ? 'Running…' : edited ? 'Run edited script' : 'Run script'}
        </button>
        {aiScript && script !== aiScript && (
          <button
            type="button"
            onClick={() => setScript(aiScript)}
            disabled={busy !== null}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-[#E2E7E1] text-xs font-semibold text-[#202923] disabled:opacity-50"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Back to the AI version
          </button>
        )}
      </div>

      {error && <p className="text-[11px] text-rose-700">{error}</p>}

      {problems.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 space-y-1">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-amber-800">
            <AlertTriangle className="h-3.5 w-3.5" /> What the CAD engine found (by script line)
          </div>
          <ul className="text-[10.5px] text-amber-900 space-y-0.5 max-h-[140px] overflow-y-auto">
            {problems.map((p, i) => (
              <li key={i}>{p.replace(/^- /, '')}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="border-t border-[#E2E7E1] pt-3 space-y-2">
        <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#23483D]">
          <Wand2 className="h-3.5 w-3.5" /> Ask for a change
        </div>
        {chat.length > 0 && (
          <div className="space-y-1.5 max-h-[180px] overflow-y-auto pr-1">
            {chat.map((m, i) => (
              <div
                key={i}
                className={`text-[11px] px-3 py-2 rounded-xl ${
                  m.role === 'user' ? 'bg-[#EEF4F0] text-[#202923] ml-6' : 'bg-[#F7F8F6] text-[#202923] mr-6 border border-[#E2E7E1]'
                }`}
              >
                <span className="font-bold">{m.role === 'user' ? 'You: ' : 'Architect: '}</span>
                {m.text}
              </div>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            disabled={busy !== null}
            placeholder="e.g. make bed space 2 wider, move the kitchen next to the gate, add a prayer corner"
            className="flex-1 text-xs px-3 py-2 rounded-xl border border-[#E2E7E1] focus:outline-none focus:ring-2 focus:ring-[#23483D]/30"
          />
          <button
            type="button"
            onClick={sendMessage}
            disabled={busy !== null || !message.trim()}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#23483D] text-white text-xs font-bold disabled:opacity-50"
          >
            {busy === 'chat' ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Wand2 className="h-3.5 w-3.5" />}
            {busy === 'chat' ? 'Working…' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DesignScriptPanel;
