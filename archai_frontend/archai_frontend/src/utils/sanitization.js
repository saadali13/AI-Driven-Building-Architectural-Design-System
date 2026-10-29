/**
 * Input sanitization, name format validation, and vulgarity/placeholder filter.
 * ArchAI Studio — Security & Sanitization Utility (Supervised by Dr. Aamer Nadeem - CUST)
 */

// Regex rule: Only alphabetic characters, spaces, hyphens, and apostrophes.
export const NAME_REGEX = /^[a-zA-Z\s'-]+$/;

// Prohibited placeholder terms, fake names, and profanity blocklist (English & Romanized)
export const PROHIBITED_TERMS = [
  // Generic placeholders / fake terms
  'test', 'testing', 'tester', 'admin', 'administrator', 'root', 'unknown', 
  'anonymous', 'null', 'undefined', 'placeholder', 'dummy', 'fake', 'sample', 
  'user', 'default', 'asdf', 'qwerty', 'noname', 'no name', 'none',

  // Common profanities, vulgar terms & slurs (English)
  'fuck', 'fucker', 'fucking', 'shit', 'bullshit', 'bitch', 'bastard', 
  'asshole', 'dick', 'pussy', 'cunt', 'cock', 'whore', 'slut', 'nigger', 
  'nigga', 'faggot', 'retard', 'piss', 'crap', 'twat', 'wanker', 'prick',

  // Romanized local profane & offensive terms
  'harami', 'haramkhor', 'kameena', 'kamina', 'chutiya', 'chutia', 
  'gandu', 'gandoo', 'bhenchod', 'bc', 'madarchod', 'mc', 'kanjar', 
  'dallal', 'lanat', 'lanati', 'kuttey', 'kutta', 'kutiya', 'ullu', 'bhadwa'
];

/**
 * Sanitizes input string to prevent XSS and strip unsafe characters.
 * @param {string} input 
 * @returns {string}
 */
export function sanitizeInput(input) {
  if (typeof input !== 'string') return '';
  return input
    .replace(/[<>]/g, '') // Strip < and >
    .trim();
}

/**
 * Validates a user's full legal name against format rules and vulgarity filters.
 * @param {string} name 
 * @returns {{ isValid: boolean, error: string | null }}
 */
export function validateFullName(name) {
  if (!name || typeof name !== 'string') {
    return {
      isValid: false,
      error: 'Please enter your full legal name.'
    };
  }

  const trimmed = name.trim();

  // Length constraints
  if (trimmed.length < 2) {
    return {
      isValid: false,
      error: 'Full name must be at least 2 characters.'
    };
  }

  if (trimmed.length > 50) {
    return {
      isValid: false,
      error: 'Full name cannot exceed 50 characters.'
    };
  }

  // Format validation: only letters, spaces, hyphens, and apostrophes
  if (!NAME_REGEX.test(trimmed)) {
    return {
      isValid: false,
      error: 'Invalid name format or prohibited words detected. Please enter your legal name.'
    };
  }

  // Vulgarity & Prohibited Term Blocklist check
  const lower = trimmed.toLowerCase();
  const words = lower.split(/[\s'-]+/).filter(Boolean);

  for (const term of PROHIBITED_TERMS) {
    // Check whole word match or exact substring match for vulgarities
    if (lower === term || words.includes(term) || (term.length >= 4 && lower.includes(term))) {
      return {
        isValid: false,
        error: 'Invalid name format or prohibited words detected. Please enter your legal name.'
      };
    }
  }

  return {
    isValid: true,
    error: null
  };
}
