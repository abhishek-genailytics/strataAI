import React from 'react';
import { InputProps } from '../../types';

export const Input: React.FC<InputProps> = ({
  label,
  placeholder,
  type = 'text',
  value,
  onChange,
  error,
  disabled = false,
  required = false,
  className = '',
}) => {
  const inputClasses = `
    block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 
    focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm
    ${error 
      ? 'border-red-300 text-red-900 focus:ring-red-500 focus:border-red-500' 
      : 'border-gray-300 text-gray-900'
    }
    ${disabled ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'}
    ${className}
  `;

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        type={type}
        className={inputClasses}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
        required={required}
      />
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};
