import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2, Loader2, MessageSquare, RotateCcw, SkipForward, Sparkles } from 'lucide-react';
import { apiService } from '../../services/apiService';

/**
 * Guided interview with the AI architect (pure text-based LLM interview on the exact studio UI).
 * The client describes the house in their own words; the AI civil architect then asks only what the description
 * leaves open based on the place, plot size, and desires, one question at a time in text, updating the brief.
 */

interface Question {
  id: string;
  question: string;
  why?: string;
  required: boolean;
  free_text?: { placeholder: string; template: string } | null;
  source?: string;
}

interface Props {
  onComplete: (brief: string) => void;
  onBack: () => void;
  busy?: boolean;
  error?: string | null;
  seed?: string;
}

export const GuidedInterview: React.FC<Props> = ({ onComplete, onBack, busy, error, seed }) => {
  const [description, setDescription] = useState(seed || '');
  const [started, setStarted] = useState(false);
  const [brief, setBrief] = useState('');
  const [answered, setAnswered] = useState<string[]>([]);
  const [log, setLog] = useState<{ q: string; a: string }[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [ready, setReady] = useState(false);
  const [understood, setUnderstood] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [freeText, setFreeText] = useState('');

  const refresh = async (
    text: string,
    ids: string[],
    currentLog: { q: string; a: string }[],
    latestMessage?: string,
  ) => {
    setLoading(true);
    setErr(null);
    try {
      const history: Array<{ role: string; text: string }> = [];
      for (const item of currentLog) {
        if (item.q) history.push({ role: 'architect', text: item.q });
        if (item.a) history.push({ role: 'user', text: item.a });
      }
      const r = await apiService.interviewBrief({
        prompt: text,
        skipped: ids,
        history,
        message: latestMessage,
      });
      if (r.compiled_brief) {
        setBrief(r.compiled_brief);
      }
      setQuestions(r.questions || []);
      setReady(!!r.ready);
      setUnderstood(r.understood_as || (Array.isArray(r.understood) ? r.understood.join(' · ') : ''));
    } catch (e: any) {
      setErr(e?.message || 'The architect could not be reached - check that the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const queue: Question[] = questions.filter((q) => !answered.includes(q.id));
  const current = queue[0];
  const stillNeeded = queue.filter((q) => q.required);

  const start = async () => {
    const text = description.trim();
    setBrief(text);
    setStarted(true);
    setLog([]);
    setAnswered([]);
    setQuestions([]);
    await refresh(text, [], []);
  };

  const answerFreeText = async (q: Question) => {
    const text = freeText.trim();
    if (!text) return;
    const template = q.free_text?.template || '{answer}';
    let sentence = template.replace('{answer}', text);
    if (!/[.!?]$/.test(sentence)) sentence += '.';
    const next = `${brief}${brief ? ' ' : ''}${sentence}`.trim();
    const ids = [...answered, q.id];
    const nextLog = [...log, { q: q.question, a: text }];
    setBrief(next);
    setAnswered(ids);
    setLog(nextLog);
    setFreeText('');
    await refresh(next, ids, nextLog, text);
  };

  const skipQuestion = async (q: Question) => {
    const ids = [...answered, q.id];
    const nextLog = [...log, { q: q.question, a: 'Let the architect decide' }];
    setAnswered(ids);
    setLog(nextLog);
    setFreeText('');
    await refresh(brief, ids, nextLog, 'Let the architect decide this part.');
  };

  if (!started) {
    return (
      <div className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-10 shadow-xs space-y-6">
        <div>
          <h2 className="text-xl font-bold text-[#202923] font-heading flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-[#23483D]" />
            Interview with the Architect
          </h2>
          <p className="text-xs text-[#68736C] mt-1 leading-relaxed">
            Describe your house in your own words - as much or as little as you like. The architect then asks only what your
            description leaves open (plot size, floors, where the staircase goes, bedrooms per floor ...). Nothing is
            pre-selected, and you can let the architect decide anything that is optional.
          </p>
        </div>
        <textarea
          rows={5}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. A family home for my parents and two kids. My mother can't climb stairs. We pray five times a day and have guests often."
          className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl p-4 text-xs text-[#202923] leading-relaxed focus:outline-none focus:border-[#23483D]"
        />
        <div className="flex flex-col-reverse sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-[#E2E7E1]">
          <button
            onClick={onBack}
            className="px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] text-xs font-semibold flex items-center justify-center gap-1.5"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back</span>
          </button>
          <button
            onClick={start}
            disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] disabled:opacity-60 text-white text-xs font-semibold shadow-sm flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            <span>{description.trim() ? 'Start the interview' : 'Start without a description'}</span>
          </button>
        </div>
        {err && <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">{err}</div>}
      </div>
    );
  }

  return (
    <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 sm:p-8 shadow-xs space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E2E7E1] pb-4">
        <h2 className="text-lg font-bold text-[#202923] font-heading flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-[#23483D]" />
          Interview with the Architect
        </h2>
        <button
          onClick={() => { setStarted(false); setLog([]); setAnswered([]); setQuestions([]); }}
          className="px-3 py-1.5 rounded-xl border border-[#E2E7E1] text-[#68736C] hover:text-[#202923] text-xs font-semibold flex items-center gap-1.5 self-start"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span>Start over</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Conversation */}
        <div className="lg:col-span-2 space-y-3 min-w-0">
          {log.map((m, i) => (
            <div key={i} className="space-y-1.5 text-xs">
              <div className="p-3 rounded-xl bg-[#F7F7F2] border border-[#E2E7E1] text-[#202923]">
                <span className="font-bold text-[#23483D]">Architect: </span>{m.q}
              </div>
              <div className="p-3 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] text-[#202923] ml-6 sm:ml-12">
                <span className="font-bold">You: </span>{m.a}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-[#68736C] p-3">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>The architect is reading your brief...</span>
            </div>
          )}

          {!loading && current && (
            <div className="p-4 sm:p-5 rounded-2xl border-2 border-[#23483D]/30 bg-white space-y-3 text-xs">
              <div className="flex items-start justify-between gap-3">
                <p className="font-bold text-sm text-[#202923]">{current.question}</p>
                <span className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-bold ${current.required ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-[#68736C]'}`}>
                  {current.required ? 'Needed' : current.source === 'ai' ? "Architect's question" : 'Optional'}
                </span>
              </div>
              {current.why && <p className="text-[#68736C] leading-relaxed">{current.why}</p>}

              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  value={freeText}
                  onChange={(e) => setFreeText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') answerFreeText(current); }}
                  placeholder={current.free_text?.placeholder || 'Type your answer in your own words...'}
                  className="flex-1 min-w-0 bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-[#23483D]"
                />
                <button
                  type="button"
                  disabled={!freeText.trim()}
                  onClick={() => answerFreeText(current)}
                  className="px-4 py-2 rounded-xl border border-[#23483D] text-[#23483D] hover:bg-[#EEF4F0] disabled:opacity-50 font-semibold"
                >
                  Use my answer
                </button>
              </div>

              {!current.required && (
                <button
                  type="button"
                  onClick={() => skipQuestion(current)}
                  className="text-[#68736C] hover:text-[#202923] font-semibold flex items-center gap-1"
                >
                  <SkipForward className="h-3.5 w-3.5" />
                  Skip - let the architect decide
                </button>
              )}
            </div>
          )}

          {!loading && !current && (
            <div className="p-4 rounded-2xl bg-[#EEF4F0] border border-[#DCE7DE] text-xs text-[#23483D] font-semibold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              That is everything I need - review the brief and design.
            </div>
          )}
          {err && <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">{err}</div>}
        </div>

        {/* The brief being built */}
        <div className="space-y-3 text-xs min-w-0">
          <div className="p-4 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-2">
            <p className="font-bold text-[#202923]">Your brief so far</p>
            <textarea
              rows={8}
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              onBlur={() => refresh(brief, answered, log)}
              className="w-full bg-white border border-[#E2E7E1] rounded-xl p-3 text-xs leading-relaxed focus:outline-none focus:border-[#23483D]"
            />
            <p className="text-[10px] text-[#68736C]">You can edit it directly - the design is generated from exactly this text.</p>
          </div>
          {understood && (
            <div className="p-4 rounded-2xl bg-white border border-[#E2E7E1] space-y-1">
              <p className="font-bold text-[#202923]">Understood so far</p>
              <p className="text-[#202923] leading-relaxed">{understood}</p>
            </div>
          )}
          {stillNeeded.length > 0 && (
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800">
              Still needed: {stillNeeded.map((q) => q.question.replace(/\?$/, '')).join('; ')}
            </div>
          )}
          {error && <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700">{error}</div>}
          <button
            type="button"
            disabled={!ready || loading || busy || !brief.trim()}
            onClick={() => onComplete(brief)}
            className="w-full px-5 py-3 rounded-xl bg-[#23483D] hover:bg-[#1A372E] disabled:opacity-50 text-white font-bold shadow-sm flex items-center justify-center gap-2"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
            <span>{busy ? 'Reading your brief...' : 'Review & design'}</span>
          </button>
          <button
            onClick={onBack}
            className="w-full px-5 py-2.5 rounded-xl border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2] font-semibold flex items-center justify-center gap-1.5"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back</span>
          </button>
        </div>
      </div>
    </div>
  );
};
export default GuidedInterview;
