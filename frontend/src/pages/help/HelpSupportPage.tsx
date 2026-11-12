import React, { useState } from 'react';
import {
  HelpCircle,
  BookOpen,
  Send,
  CheckCircle2,
  FileQuestion,
  ExternalLink,
  Building,
  ShieldCheck,
  Check
} from 'lucide-react';

export const HelpSupportPage: React.FC = () => {
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketMessage, setTicketMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticketSubject && ticketMessage) {
      setSubmitted(true);
      setTimeout(() => {
        setTicketSubject('');
        setTicketMessage('');
      }, 3000);
    }
  };

  return (
    <div className="space-y-8 pb-12 max-w-5xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5">
        <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
          Help & Architectural Support
        </h1>
        <p className="text-xs text-[#68736C] mt-1">
          Documentation on Pakistani building bylaws (CDA/LDA/DHA), AI prompt engineering, and support requests.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* FAQs */}
        <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 sm:p-7 space-y-4 text-xs shadow-xs">
          <h2 className="text-sm font-bold text-[#202923] font-heading flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-[#23483D]" />
            Frequently Asked Questions
          </h2>

          <div className="space-y-3">
            <div className="p-3.5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
              <p className="font-bold text-[#202923]">How do setback calculations work for 10 Marla plots?</p>
              <p className="text-[#68736C] leading-relaxed text-[11px]">
                Under CDA and LDA building regulations, a 10 Marla (35 &times; 65 ft) plot requires a front setback of 8 ft and rear setback of 5 ft to guarantee structural ventilation and natural lighting.
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
              <p className="font-bold text-[#202923]">Can I modify room dimensions after AI generation?</p>
              <p className="text-[#68736C] leading-relaxed text-[11px]">
                Yes, click "Edit Requirements" on your project page or duplicate the design to synthesize alternative layouts with adjusted dimensional constraints.
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#F7F7F2] border border-[#E2E7E1] space-y-1">
              <p className="font-bold text-[#202923]">What is the Pakistani "dirty kitchen" requirement?</p>
              <p className="text-[#68736C] leading-relaxed text-[11px]">
                A cultural standard in Pakistani residential homes (DHA/Bahria) providing a secondary preparation area for heavy cooking with direct exhaust to rear open airwells.
              </p>
            </div>
          </div>
        </div>

        {/* Submit Ticket */}
        <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 sm:p-7 space-y-4 text-xs shadow-xs">
          <h2 className="text-sm font-bold text-[#202923] font-heading flex items-center gap-2">
            <Send className="h-4 w-4 text-[#23483D]" />
            Contact Platform Support
          </h2>

          {submitted ? (
            <div className="p-6 rounded-2xl bg-[#DCE7DE]/50 border border-[#23483D]/30 text-[#23483D] space-y-2 text-center">
              <CheckCircle2 className="h-8 w-8 text-[#23483D] mx-auto" />
              <p className="font-bold text-sm">Inquiry Dispatched</p>
              <p className="text-[#68736C] text-xs">Our engineering and architectural team will respond via your registered email address.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-[#202923] font-medium mb-1.5">Subject</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 5 Marla setback query or DXF export question"
                  value={ticketSubject}
                  onChange={(e) => setTicketSubject(e.target.value)}
                  className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3.5 py-2 text-[#202923] focus:outline-none focus:border-[#23483D] transition-colors"
                />
              </div>

              <div>
                <label className="block text-[#202923] font-medium mb-1.5">Message</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Describe your design issue or feedback..."
                  value={ticketMessage}
                  onChange={(e) => setTicketMessage(e.target.value)}
                  className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3.5 py-2 text-[#202923] focus:outline-none focus:border-[#23483D] transition-colors"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1a362d] text-white font-semibold transition-colors shadow-xs"
              >
                Submit Support Ticket
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
