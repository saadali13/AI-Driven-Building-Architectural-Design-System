import React, { useState } from 'react';
import { 
  MessageSquare, 
  Star, 
  Send, 
  CheckCircle2, 
  Sparkles, 
  ThumbsUp, 
  Building2, 
  Box, 
  DollarSign, 
  Layers, 
  User, 
  Calendar,
  Check,
  Filter,
  Trash2
} from 'lucide-react';
import { useAuth, ROLES } from '../../context/AuthContext';
import { getStoredFeedback, saveUserFeedback, saveAdminNotification, deleteUserFeedback } from '../../utils/feedbackStore';

export default function FeedbackModule() {
  const { user } = useAuth();
  const [reviews, setReviews] = useState(() => getStoredFeedback());
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [category, setCategory] = useState('3D WebGL & Elevation');
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toastMsg, setToastMsg] = useState('');

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3500);
  };

  const handleRemoveReview = (reviewId, authorName) => {
    if (window.confirm(`Are you sure you want to permanently delete feedback submitted by "${authorName}"?`)) {
      const updated = deleteUserFeedback(reviewId);
      setReviews(updated);
      showToast(`Feedback review from "${authorName}" has been permanently deleted.`);
    }
  };


  const handleSubmit = (e) => {
    e.preventDefault();
    if (!comment.trim()) return;

    setIsSubmitting(true);
    setTimeout(() => {
      const newReview = {
        id: `fb_${Date.now()}`,
        author: user?.name || 'Authenticated User',
        email: user?.email || 'user@archai.design',
        role: user?.role || 'HOMEOWNER',
        rating,
        category,
        comment: comment.trim(),
        date: 'Just now',
        createdAt: new Date().toISOString(),
        status: 'Pending',
        likes: 0
      };

      // 1. Permanently save to persistent database store
      saveUserFeedback(newReview);

      // 2. Dispatch high-priority alert to System Administrator
      saveAdminNotification({
        id: `notif_${Date.now()}`,
        title: `New Platform Feedback (${rating} Stars)`,
        message: `${user?.name || 'User'} (${user?.role || 'HOMEOWNER'}) submitted feedback for ${category}: "${comment.trim()}"`,
        type: 'feedback',
        timestamp: new Date().toISOString(),
        read: false
      });

      // 3. Update local state
      setReviews(getStoredFeedback());
      setComment('');
      setRating(5);
      setIsSubmitting(false);
      showToast('Thank you! Your feedback has been saved to database and sent to System Admin.');
    }, 600);
  };


  return (
    <div className="w-full max-w-5xl mx-auto space-y-8 text-slate-900 font-sans">
      
      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2.5 px-5 py-3.5 bg-slate-900 text-white rounded-2xl shadow-2xl text-sm font-semibold animate-in fade-in">
          <Check className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-blue-50 border border-blue-100 text-blue-600">
              <MessageSquare className="w-6 h-6" />
            </div>
            <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Platform Feedback &amp; Reviews</h1>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed max-w-2xl">
            Help our engineering team improve the generative BIM algorithms, localized PKR price indexes, and 3D rendering accuracy.
          </p>
        </div>
      </div>

      {/* Feedback Submission Card */}
      <form onSubmit={handleSubmit} className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
        <h3 className="text-base font-bold text-slate-900">Submit Your Experience</h3>

        {/* Rating Stars */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
            Overall Rating *
          </label>
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(star)}
                className="p-1 text-slate-300 hover:scale-110 transition cursor-pointer"
              >
                <Star
                  className={`w-7 h-7 ${
                    (hoverRating || rating) >= star
                      ? 'fill-amber-400 text-amber-400'
                      : 'text-slate-300'
                  }`}
                />
              </button>
            ))}
            <span className="text-xs font-bold text-slate-600 ml-2 font-mono">
              {rating} of 5 Stars
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
              Feedback Category *
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white cursor-pointer"
            >
              <option value="3D WebGL & Elevation">3D WebGL &amp; Elevation Rendering</option>
              <option value="AI NLP Vector Search">AI Spatial Vector Search &amp; NLP</option>
              <option value="PKR Cost Matrix">PKR Cost Matrix &amp; BOQ Accuracy</option>
              <option value="Municipal Bylaws">Municipal Bylaws &amp; Society Setbacks</option>
              <option value="General UI/UX">General Interface &amp; Navigation</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
              Submitting As
            </label>
            <input
              type="text"
              disabled
              value={`${user?.name || 'Authenticated User'} (${user?.role || 'HOMEOWNER'})`}
              className="w-full px-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-sm text-slate-600 font-medium"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
            Detailed Review &amp; Recommendations *
          </label>
          <textarea
            rows={4}
            required
            placeholder="Share specific feedback regarding layout generation, spatial dimensions, material prices, or rendering performance..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white"
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl transition shadow-md shadow-blue-500/20 flex items-center gap-2 cursor-pointer disabled:opacity-50 hover:scale-[1.01]"
          >
            <Send className="w-4 h-4" />
            <span>{isSubmitting ? 'Submitting Review...' : 'Submit Feedback'}</span>
          </button>
        </div>
      </form>

      {/* Community Reviews List */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-slate-900">Recent User Feedback</h3>
        <div className="space-y-4">
          {reviews.map((r) => (
            <div key={r.id} className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                    {r.author.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">{r.author}</h4>
                    <span className="text-xs text-slate-500">{r.role} • {r.date}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-xs font-mono font-bold">
                    {r.category}
                  </span>
                  <div className="flex items-center">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-4 h-4 ${
                          i < r.rating ? 'fill-amber-400 text-amber-400' : 'text-slate-200'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>

              <p className="text-sm text-slate-700 leading-relaxed">
                "{r.comment}"
              </p>

              {user?.role === ROLES.SYSTEM_ADMIN && (
                <div className="flex justify-end pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => handleRemoveReview(r.id, r.author)}
                    className="px-3.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 shadow-2xs"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Remove Review</span>
                  </button>
                </div>
              )}
            </div>

          ))}
        </div>
      </div>

    </div>
  );
}
