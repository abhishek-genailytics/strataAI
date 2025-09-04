export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

export interface PasswordStrength {
  score: number;
  isValid: boolean;
  feedback: string[];
}

export interface FormValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

export type Validator<T = any> = (value: T) => ValidationResult;

/**
 * Validates an email address
 */
export const validateEmail = (email: string): ValidationResult => {
  if (!email || email.trim() === "") {
    return { isValid: false, error: "Email is required" };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { isValid: false, error: "Please enter a valid email address" };
  }

  return { isValid: true };
};

/**
 * Validates a password
 */
export const validatePassword = (password: string): ValidationResult => {
  if (!password || password.trim() === "") {
    return { isValid: false, error: "Password is required" };
  }

  if (password.length < 8) {
    return {
      isValid: false,
      error: "Password must be at least 8 characters long",
    };
  }

  return { isValid: true };
};

/**
 * Validates password confirmation
 */
export const validatePasswordConfirmation = (
  password: string,
  confirmPassword: string
): ValidationResult => {
  if (!confirmPassword || confirmPassword.trim() === "") {
    return { isValid: false, error: "Please confirm your password" };
  }

  if (password !== confirmPassword) {
    return { isValid: false, error: "Passwords do not match" };
  }

  return { isValid: true };
};

/**
 * Validates a name
 */
export const validateName = (name: string): ValidationResult => {
  if (!name || name.trim() === "") {
    return { isValid: false, error: "Name is required" };
  }

  if (name.trim().length < 2) {
    return { isValid: false, error: "Name must be at least 2 characters long" };
  }

  if (name.length > 50) {
    return { isValid: false, error: "Name must be less than 50 characters" };
  }

  return { isValid: true };
};

/**
 * Calculates password strength and provides feedback
 */
export const getPasswordStrength = (password: string): PasswordStrength => {
  const feedback: string[] = [];
  let score = 0;

  if (!password || password.trim() === "") {
    return {
      score: 0,
      isValid: false,
      feedback: ["Password is required"],
    };
  }

  // Length check
  if (password.length >= 8) {
    score += 1;
  } else {
    feedback.push("Use at least 8 characters");
  }

  // Lowercase check
  if (/[a-z]/.test(password)) {
    score += 1;
  } else {
    feedback.push("Add lowercase letters");
  }

  // Uppercase check
  if (/[A-Z]/.test(password)) {
    score += 1;
  } else {
    feedback.push("Add uppercase letters");
  }

  // Number check
  if (/\d/.test(password)) {
    score += 1;
  } else {
    feedback.push("Add numbers");
  }

  // Special character check
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    score += 1;
  } else {
    feedback.push("Add special characters");
  }

  // Additional checks for very weak passwords
  if (password.length < 6) {
    feedback.push("Password is too short");
  }

  if (password === password.toLowerCase() && password.length > 0) {
    feedback.push("Consider using mixed case");
  }

  if (!/\d/.test(password) && password.length > 0) {
    feedback.push("Consider adding numbers");
  }

  return {
    score,
    isValid: score >= 3,
    feedback: feedback.length > 0 ? feedback : ["Password looks good!"],
  };
};

/**
 * Validates a form with multiple fields
 */
export const validateForm = <T extends Record<string, any>>(
  fields: T,
  validators: Record<keyof T, Validator>
): FormValidationResult => {
  const errors: Record<string, string> = {};
  let isValid = true;

  for (const [fieldName, value] of Object.entries(fields)) {
    const validator = validators[fieldName as keyof T];
    if (validator) {
      const result = validator(value);
      if (!result.isValid) {
        errors[fieldName] = result.error || "Invalid value";
        isValid = false;
      }
    }
  }

  return { isValid, errors };
};
