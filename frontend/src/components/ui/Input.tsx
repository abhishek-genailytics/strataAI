import React from 'react';
import { InputProps } from '../../types';

export const Input: React.FC<InputProps> = ({
  label,
  placeholder,
  type = 'text',
  value,
  onChange,
  onBlur,
  error,
  disabled = false,
  required = false,
  className = '',
}) => {
  const inputClasses = `
    block w-full px-4 py-3 border rounded-xl shadow-sm placeholder-slate-400 
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm
    transition-all duration-200
    ${error 
      ? 'border-red-300 text-red-900 focus:ring-red-500 focus:border-red-500 bg-red-50' 
      : 'border-slate-300 text-slate-900 bg-white hover:border-slate-400'
    }
    ${disabled ? 'bg-slate-50 cursor-not-allowed opacity-60' : ''}
    ${className}
  `;

  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-semibold text-slate-700">
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
        onBlur={onBlur}
        disabled={disabled}
        required={required}
      />
      {error && (
        <p className="text-sm text-red-600 flex items-center">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
};