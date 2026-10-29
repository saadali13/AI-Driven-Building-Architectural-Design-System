import React, { useState } from 'react';
import {
  HelpCircle,
  BookOpen,
  Send,
  CheckCircle2,
  AlertCircle,
  FileText,
  MapPin,
  Building,
} from 'lucide-react';

export const HelpPage: React.FC = () => {
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketMessage, setTicketMessage] = useState('');
  const [ticketEmail, setTicketEmail] = useState('');

  const handleSupportSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticketSubject && ticketMessage && ticketEmail) {
      setFormSubmitted(true);
      setTimeout(() => {
        setTicketSubject('');
        setTicketMessage('');
        setTicketEmail('');
      }, 3000);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Header */}
      <div>
        <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-teal-950 text-teal-300 border border-teal-800">
          KNOWLEDGE BASE & BYLAWS
        </span>
        <h1 className="text-3xl font-bold text-white mt-2 font-heading">Help Center & Pakistani Building Bylaws</h1>
        <p className="text-sm text-slate-400 mt-1">
          Reference guides for residential setback rules, covered area ratios, and platform support.
        </p>
      </div>

      {/* Bylaw Reference Tables */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold text-white font-heading flex items-center gap-2">
          <Building className="h-5 w-5 text-teal-400" />
          Standard Pakistani Municipal Bylaws Quick Reference
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* CDA Islamabad */}
          <div id="cda" className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-base">CDA Islamabad</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-teal-400">ICT Zone 1 & 2</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-2">
              <li>• <strong>5 Marla:</strong> Front setback 5 ft, Rear 3 ft, Max height 35 ft.</li>
              <li>• <strong>10 Marla:</strong> Front setback 7.5 ft, Rear 5 ft, Max height 38 ft.</li>
              <li>• <strong>1 Kanal:</strong> Front setback 10 ft, Rear 5 ft, Sides 5 ft.</li>
              <li>• <strong>Ground Coverage:</strong> 65% to 70% allowable footprint.</li>
            </ul>
          </div>

          {/* LDA Lahore */}
          <div id="lda" className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-base">LDA Lahore</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-teal-400">Punjab Urban</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-2">
              <li>• <strong>5 Marla:</strong> Mandatory 5 ft front open space.</li>
              <li>• <strong>10 Marla:</strong> Front 7 ft, rear 5 ft open space for airwell.</li>
              <li>• <strong>1 Kanal:</strong> Front 10 ft, sides minimum 4 ft clearance.</li>
              <li>• <strong>Basement:</strong> Permitted with 5 ft structural clearance.</li>
            </ul>
          </div>

          {/* DHA Standards */}
          <div id="dha" className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-base">DHA Guidelines</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-teal-400">All Chapters</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-2">
              <li>• <strong>Porch Gate:</strong> 14 to 18 ft wide, inward swing mandatory.</li>
              <li>• <strong>Plinth Level:</strong> +2.5 to +3.5 ft above crowned road center.</li>
              <li>• <strong>Parapet:</strong> Minimum 3 ft 6 inches safety height.</li>
              <li>• <strong>Rooftop Mumty:</strong> Maximum 10 ft height from roof slab.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Support Ticket Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white font-heading">Submit Inquiry or Support Request</h2>
          <p className="text-xs text-slate-400 mt-1">
            Questions regarding layout calculations, template requests, or academic FYP demonstration queries.
          </p>
        </div>

        {formSubmitted ? (
          <div className="p-4 rounded-xl bg-teal-950/80 border border-teal-500 flex items-center gap-3 text-teal-300 text-xs">
            <CheckCircle2 className="h-5 w-5 text-teal-400 shrink-0" />
            <div>
              <p className="font-bold">Inquiry Sent Successfully!</p>
              <p className="text-slate-300">Our FYP academic team has received your ticket and will respond via email.</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSupportSubmit} className="space-y-4 max-w-2xl">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-300 font-medium mb-1">Your Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="name@example.pk"
                  value={ticketEmail}
                  onChange={(e) => setTicketEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-300 font-medium mb-1">Inquiry Subject</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 7 Marla CDA setback question"
                  value={ticketSubject}
                  onChange={(e) => setTicketSubject(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-300 font-medium mb-1">Detailed Message</label>
              <textarea
                required
                rows={4}
                placeholder="Describe your design requirement, society guidelines, or question..."
                value={ticketMessage}
                onChange={(e) => setTicketMessage(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-teal-500"
              />
            </div>

            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold shadow-md flex items-center gap-2 transition-colors"
            >
              <Send className="h-3.5 w-3.5" />
              <span>Send Support Ticket</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
