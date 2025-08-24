export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

export interface PasswordStrength {
  score: number; // 0-4
  feedback: string[];
  isValid: boolean;
}

// Email validation
export const validateEmail = (email: string): ValidationResult => {
  if (!email) {
    return { isValid: false, error: 'Email is required' };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Please enter a valid email address' };
  }

  return { isValid: true };
};

// Password validation with strength checking
export const validatePassword = (password: string): ValidationResult => {
  if (!password) {
    return { isValid: false, error: 'Password is required' };
  }

  if (password.length < 8) {
    return { isValid: false, error: 'Password must be at least 8 characters long' };
  }

  return { isValid: true };
};

// Password strength assessment
export const getPasswordStrength = (password: string): PasswordStrength => {
  if (!password) {
    return { score: 0, feedback: ['Password is required'], isValid: false };
  }

  let score = 0;
  const feedback: string[] = [];

  // Length check
  if (password.length >= 8) {
    score += 1;
  } else {
    feedback.push('Use at least 8 characters');
  }

  // Lowercase check
  if (/[a-z]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Add lowercase letters');
  }

  // Uppercase check
  if (/[A-Z]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Add uppercase letters');
  }

  // Number check
  if (/\d/.test(password)) {
    score += 1;
  } else {
    feedback.push('Add numbers');
  }

  // Special character check
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Add special characters');
  }

  // Determine overall strength
  let strengthText = '';
  switch (score) {
    case 0:
    case 1:
      strengthText = 'Very weak';
      break;
    case 2:
      strengthText = 'Weak';
      break;
    case 3:
      strengthText = 'Fair';
      break;
    case 4:
      strengthText = 'Good';
      break;
    case 5:
      strengthText = 'Strong';
      break;
  }

  if (feedback.length === 0) {
    feedback.push(`Password strength: ${strengthText}`);
  }

  return {
    score: Math.min(score, 4), // Cap at 4 for UI display
    feedback,
    isValid: score >= 3, // Require at least "Fair" strength
  };
};

// Confirm password validation
export const validatePasswordConfirmation = (
  password: string,
  confirmPassword: string
): ValidationResult => {
  if (!confirmPassword) {
    return { isValid: false, error: 'Please confirm your password' };
  }

  if (password !== confirmPassword) {
    return { isValid: false, error: 'Passwords do not match' };
  }

  return { isValid: true };
};

// Name validation
export const validateName = (name: string): ValidationResult => {
  if (!name) {
    return { isValid: false, error: 'Name is required' };
  }

  if (name.trim().length < 2) {
    return { isValid: false, error: 'Name must be at least 2 characters long' };
  }

  if (name.trim().length > 50) {
    return { isValid: false, error: 'Name must be less than 50 characters' };
  }

  return { isValid: true };
};

// Form validation helper
export const validateForm = (
  fields: Record<string, any>,
  validators: Record<string, (value: any) => ValidationResult>
): { isValid: boolean; errors: Record<string, string> } => {
  const errors: Record<string, string> = {};
  let isValid = true;

  Object.keys(validators).forEach((field) => {
    const result = validators[field](fields[field]);
    if (!result.isValid && result.error) {
      errors[field] = result.error;
      isValid = false;
    }
  });

  return { isValid, errors };
};
