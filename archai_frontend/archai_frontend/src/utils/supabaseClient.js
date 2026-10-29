import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://hktnxnxgwjzopvhbgino.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhrdG54bnhnd2p6b3B2aGJnaW5vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIwNjc5MzMsImV4cCI6MjEwNzY0MzkzM30.vqj82kAFbYpDtQceKEQO5TxQ4rFGJ5eqzIekEpuWQZM';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

/**
 * Register a new user with Supabase and send real verification email.
 */
export async function registerWithEmail({ email, password, fullName, role, phone = '', organization = '' }) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: fullName,
        role: role,
        phone: phone,
        organization: organization,
      },
      emailRedirectTo: window.location.origin,
    },
  });

  if (error) {
    throw error;
  }

  return data;
}

/**
 * Log in an existing user with Supabase.
 */
export async function loginWithEmail(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    throw error;
  }

  return data;
}

/**
 * Resend verification email for unconfirmed accounts.
 */
export async function resendConfirmationEmail(email) {
  const { data, error } = await supabase.auth.resend({
    type: 'signup',
    email,
    options: {
      emailRedirectTo: window.location.origin,
    },
  });

  if (error) {
    throw error;
  }

  return data;
}

/**
 * Log out user from Supabase.
 */
export async function logoutUser() {
  const { error } = await supabase.auth.signOut();
  if (error) {
    console.warn('Supabase signout warning:', error);
  }
}
