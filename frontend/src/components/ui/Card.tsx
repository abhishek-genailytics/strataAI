import React from 'react';
import { CardProps } from '../../types';

export const Card: React.FC<CardProps> = ({
  children,
  title,
  className = '',
  padding = true,
  onClick,
}) => {
  const baseClasses = 'bg-white overflow-hidden shadow-lg rounded-xl border border-slate-200 transition-all duration-200';
  const hoverClasses = onClick ? 'cursor-pointer hover:shadow-xl hover:border-slate-300 transform hover:-translate-y-0.5' : '';
  const paddingClasses = padding ? 'px-6 py-6' : '';
  
  return (
    <div 
      className={`${baseClasses} ${hoverClasses} ${className}`}
      onClick={onClick}
    >
      {title && (
        <div className="px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-white">
          <h3 className="text-lg leading-6 font-bold text-slate-900">
            {title}
          </h3>
        </div>
      )}
      <div className={paddingClasses}>
        {children}
      </div>
    </div>
  );
};