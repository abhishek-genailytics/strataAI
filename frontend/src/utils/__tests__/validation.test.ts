import {
  validateEmail,
  validatePassword,
  getPasswordStrength,
  validatePasswordConfirmation,
  validateName,
  validateForm,
} from '../validation';

describe('Validation Utils', () => {
  describe('validateEmail', () => {
    it('should validate correct email addresses', () => {
      const validEmails = [
        'test@example.com',
        'user.name@domain.co.uk',
        'user+tag@example.org',
        'user123@test-domain.com',
      ];

      validEmails.forEach(email => {
        const result = validateEmail(email);
        expect(result.isValid).toBe(true);
        expect(result.error).toBeUndefined();
      });
    });

    it('should reject invalid email addresses', () => {
      const invalidEmails = [
        '',
        'invalid-email',
        '@example.com',
        'user@',
        'user@.com',
        'user name@example.com',
      ];

      invalidEmails.forEach(email => {
        const result = validateEmail(email);
        expect(result.isValid).toBe(false);
        expect(result.error).toBeDefined();
      });
    });

    it('should require email', () => {
      const result = validateEmail('');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email is required');
    });
  });

  describe('validatePassword', () => {
    it('should validate passwords with minimum length', () => {
      const validPasswords = [
        'password123',
        'mySecurePass',
        'aB3$fG7!',
      ];

      validPasswords.forEach(password => {
        const result = validatePassword(password);
        expect(result.isValid).toBe(true);
        expect(result.error).toBeUndefined();
      });
    });

    it('should reject passwords that are too short', () => {
      const shortPasswords = [
        '',
        '123',
        'short',
        '1234567',
      ];

      shortPasswords.forEach(password => {
        const result = validatePassword(password);
        expect(result.isValid).toBe(false);
        expect(result.error).toBeDefined();
      });
    });

    it('should require password', () => {
      const result = validatePassword('');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password is required');
    });
  });

  describe('getPasswordStrength', () => {
    it('should return very weak for empty password', () => {
      const result = getPasswordStrength('');
      expect(result.score).toBe(0);
      expect(result.isValid).toBe(false);
      expect(result.feedback).toContain('Password is required');
    });

    it('should return weak for simple passwords', () => {
      const result = getPasswordStrength('password');
      expect(result.score).toBe(2);
      expect(result.isValid).toBe(false);
    });

    it('should return fair for moderately complex passwords', () => {
      const result = getPasswordStrength('Password123');
      expect(result.score).toBe(3);
      expect(result.isValid).toBe(true);
    });

    it('should return strong for complex passwords', () => {
      const result = getPasswordStrength('MySecure123!');
      expect(result.score).toBe(4);
      expect(result.isValid).toBe(true);
    });

    it('should provide helpful feedback', () => {
      const result = getPasswordStrength('pass');
      expect(result.feedback.length).toBeGreaterThan(0);
      expect(result.feedback.some(f => f.includes('8 characters'))).toBe(true);
    });
  });

  describe('validatePasswordConfirmation', () => {
    it('should validate matching passwords', () => {
      const password = 'myPassword123';
      const result = validatePasswordConfirmation(password, password);
      expect(result.isValid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should reject non-matching passwords', () => {
      const result = validatePasswordConfirmation('password1', 'password2');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Passwords do not match');
    });

    it('should require confirmation password', () => {
      const result = validatePasswordConfirmation('password', '');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Please confirm your password');
    });
  });

  describe('validateName', () => {
    it('should validate proper names', () => {
      const validNames = [
        'John Doe',
        'Alice',
        'Bob Smith Jr.',
        'María García',
      ];

      validNames.forEach(name => {
        const result = validateName(name);
        expect(result.isValid).toBe(true);
        expect(result.error).toBeUndefined();
      });
    });

    it('should reject names that are too short', () => {
      const result = validateName('A');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Name must be at least 2 characters long');
    });

    it('should reject names that are too long', () => {
      const longName = 'A'.repeat(51);
      const result = validateName(longName);
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Name must be less than 50 characters');
    });

    it('should require name', () => {
      const result = validateName('');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Name is required');
    });
  });

  describe('validateForm', () => {
    it('should validate all fields and return combined results', () => {
      const fields = {
        email: 'test@example.com',
        password: 'validPassword123',
        name: 'John Doe',
      };

      const validators = {
        email: validateEmail,
        password: validatePassword,
        name: validateName,
      };

      const result = validateForm(fields, validators);
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors)).toHaveLength(0);
    });

    it('should return all validation errors', () => {
      const fields = {
        email: 'invalid-email',
        password: 'short',
        name: '',
      };

      const validators = {
        email: validateEmail,
        password: validatePassword,
        name: validateName,
      };

      const result = validateForm(fields, validators);
      expect(result.isValid).toBe(false);
      expect(Object.keys(result.errors)).toHaveLength(3);
      expect(result.errors.email).toBeDefined();
      expect(result.errors.password).toBeDefined();
      expect(result.errors.name).toBeDefined();
    });

    it('should handle partial validation', () => {
      const fields = {
        email: 'test@example.com',
        password: 'short',
      };

      const validators = {
        email: validateEmail,
        password: validatePassword,
      };

      const result = validateForm(fields, validators);
      expect(result.isValid).toBe(false);
      expect(result.errors.email).toBeUndefined();
      expect(result.errors.password).toBeDefined();
    });
  });
});
