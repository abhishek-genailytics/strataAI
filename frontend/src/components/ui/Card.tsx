import React from 'react';
import { CardProps } from '../../types';

export const Card: React.FC<CardProps> = ({
  children,
  title,
  className = '',
  padding = true,
}) => {
  const baseClasses = 'bg-white overflow-hidden shadow rounded-lg';
  const paddingClasses = padding ? 'px-4 py-5 sm:p-6' : '';
  
  return (
    <div className={`${baseClasses} ${className}`}>
      {title && (
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
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
