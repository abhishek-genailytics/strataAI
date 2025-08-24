import React from 'react';
import { TimeRangeSelectorProps } from '../../types';

const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({ value, onChange, options }) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
      <label className="text-sm font-medium text-gray-700">Time Range:</label>
      <select
        value={value.value}
        onChange={(e) => {
          const selectedOption = options.find(option => option.value === e.target.value);
          if (selectedOption) {
            onChange(selectedOption);
          }
        }}
        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};

export default TimeRangeSelector;
