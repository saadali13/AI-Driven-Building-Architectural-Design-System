/**
 * ArchAI Studio — Persistent User Feedback & Admin Notification Store
 */

const FEEDBACK_STORAGE_KEY = 'archai_submitted_user_feedback';
const ADMIN_NOTIFICATIONS_KEY = 'archai_admin_notifications';

export const INITIAL_FEEDBACK_REVIEWS = [
  {
    id: 'fb_101',
    author: 'Shahid Khan',
    email: 'shahid.arch@studio.pk',
    role: 'Lead Architect',
    rating: 5,
    category: '3D WebGL & Elevation',
    comment: 'The automated 5-marla modern elevation generation saved our studio over 12 hours of 3D modeling time. The setback bylaws compliance is spot on.',
    createdAt: '2026-02-20T10:30:00Z',
    status: 'Reviewed',
    likes: 14
  },
  {
    id: 'fb_102',
    author: 'Zubair Ahmed',
    email: 'zubair.homeowner@gmail.com',
    role: 'Homeowner / Customer',
    rating: 5,
    category: 'PKR Cost Matrix',
    comment: 'Estimated steel and cement costs in Rawalpindi with astonishing accuracy. Very helpful for budgeting our double story house.',
    createdAt: '2026-02-18T14:15:00Z',
    status: 'Reviewed',
    likes: 8
  },
  {
    id: 'fb_103',
    author: 'Bilal Malik',
    email: 'bilal.dev@capital.pk',
    role: 'Real Estate Developer',
    rating: 4,
    category: 'AI NLP Vector Search',
    comment: 'Natural language search correctly matches room schedules for multi-story residential blocks. Would love to see support for 2-Kanal farmhouses soon.',
    createdAt: '2026-02-14T09:45:00Z',
    status: 'Pending',
    likes: 19
  }
];

export function getStoredFeedback() {
  try {
    const raw = localStorage.getItem(FEEDBACK_STORAGE_KEY);
    if (raw) {
      const customReviews = JSON.parse(raw);
      return [...customReviews, ...INITIAL_FEEDBACK_REVIEWS];
    }
  } catch (e) {
    console.error('Error reading feedback store', e);
  }
  return [...INITIAL_FEEDBACK_REVIEWS];
}

export function saveUserFeedback(newReview) {
  try {
    const raw = localStorage.getItem(FEEDBACK_STORAGE_KEY);
    let customReviews = raw ? JSON.parse(raw) : [];
    customReviews = [newReview, ...customReviews];
    localStorage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify(customReviews));
  } catch (e) {
    console.error('Error saving user feedback', e);
  }
}

export function getStoredAdminNotifications() {
  try {
    const raw = localStorage.getItem(ADMIN_NOTIFICATIONS_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (e) {
    console.error('Error reading admin notifications', e);
  }
  return [];
}

export function saveAdminNotification(notification) {
  try {
    const current = getStoredAdminNotifications();
    const updated = [notification, ...current];
    localStorage.setItem(ADMIN_NOTIFICATIONS_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error('Error saving admin notification', e);
  }
}

export function deleteUserFeedback(feedbackId) {
  try {
    const currentList = getStoredFeedback();
    const filtered = currentList.filter(f => f.id !== feedbackId);
    // Keep custom reviews in localStorage minus deleted item
    const customOnly = filtered.filter(f => !INITIAL_FEEDBACK_REVIEWS.some(init => init.id === f.id));
    localStorage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify(customOnly));
    return filtered;
  } catch (e) {
    console.error('Error deleting user feedback', e);
    return getStoredFeedback();
  }
}

export function updateAdminNotificationStatus(notificationId, newStatus = 'received') {
  try {
    const current = getStoredAdminNotifications();
    const updated = current.map(item => {
      if (item.id === notificationId) {
        return { ...item, status: newStatus, read: true };
      }
      return item;
    });
    localStorage.setItem(ADMIN_NOTIFICATIONS_KEY, JSON.stringify(updated));
    return updated;
  } catch (e) {
    console.error('Error updating admin notification status', e);
    return getStoredAdminNotifications();
  }
}


