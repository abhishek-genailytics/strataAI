import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, X, Check } from "lucide-react";

export interface MultiSelectOption {
  id: string;
  label: string;
  value: string;
  description?: string;
  disabled?: boolean;
}

export interface MultiSelectProps {
  label?: string;
  placeholder?: string;
  options: MultiSelectOption[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  maxHeight?: string;
  searchable?: boolean;
  showSelectAll?: boolean;
}

export const MultiSelect: React.FC<MultiSelectProps> = ({
  label,
  placeholder = "Select options...",
  options,
  selectedValues,
  onChange,
  error,
  disabled = false,
  required = false,
  className = "",
  maxHeight = "200px",
  searchable = true,
  showSelectAll = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter options based on search term
  const filteredOptions = options.filter(
    (option) =>
      option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      option.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get selected options for display
  const selectedOptions = options.filter((option) =>
    selectedValues.includes(option.value)
  );

  // Handle option toggle
  const toggleOption = (value: string) => {
    if (disabled) return;

    const newValues = selectedValues.includes(value)
      ? selectedValues.filter((v) => v !== value)
      : [...selectedValues, value];

    onChange(newValues);
  };

  // Handle remove selected option
  const removeOption = (value: string) => {
    if (disabled) return;
    onChange(selectedValues.filter((v) => v !== value));
  };

  // Handle select all functionality
  const handleSelectAll = () => {
    if (disabled) return;

    const availableOptions = filteredOptions.filter(
      (option) => !option.disabled
    );
    const allValues = availableOptions.map((option) => option.value);

    // If all available options are selected, deselect all
    const allSelected = allValues.every((value) =>
      selectedValues.includes(value)
    );

    if (allSelected) {
      // Deselect all filtered options
      const newValues = selectedValues.filter(
        (value) => !availableOptions.some((option) => option.value === value)
      );
      onChange(newValues);
    } else {
      // Select all filtered options
      const combinedValues = [...selectedValues, ...allValues];
      const newValues = Array.from(new Set(combinedValues));
      onChange(newValues);
    }
  };

  // Check if all available options are selected
  const availableOptions = filteredOptions.filter((option) => !option.disabled);
  const allSelected =
    availableOptions.length > 0 &&
    availableOptions.every((option) => selectedValues.includes(option.value));

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Focus input when dropdown opens
  useEffect(() => {
    if (isOpen && searchable && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen, searchable]);

  const inputClasses = `
    block w-full px-4 py-3 border rounded-xl shadow-sm placeholder-slate-400 
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm
    transition-all duration-200 cursor-pointer
    ${
      error
        ? "border-red-300 text-red-900 focus:ring-red-500 focus:border-red-500 bg-red-50"
        : "border-slate-300 text-slate-900 bg-white hover:border-slate-400"
    }
    ${disabled ? "bg-slate-50 cursor-not-allowed opacity-60" : ""}
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

      <div className="relative" ref={dropdownRef}>
        {/* Selected options display */}
        <div
          className={inputClasses}
          onClick={() => !disabled && setIsOpen(!isOpen)}
        >
          <div className="flex flex-wrap gap-1 items-center min-h-[20px]">
            {selectedOptions.length > 0 ? (
              <>
                {selectedOptions.map((option) => (
                  <span
                    key={option.value}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-md"
                  >
                    {option.label}
                    {!disabled && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeOption(option.value);
                        }}
                        className="hover:bg-blue-200 rounded-full p-0.5"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    )}
                  </span>
                ))}
                {selectedOptions.length < options.length && (
                  <span className="text-slate-500 text-sm">
                    +{options.length - selectedOptions.length} more available
                  </span>
                )}
              </>
            ) : (
              <span className="text-slate-400">{placeholder}</span>
            )}
          </div>
          <ChevronDown
            className={`absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400 transition-transform duration-200 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </div>

        {/* Dropdown */}
        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-slate-300 rounded-xl shadow-lg max-h-60 overflow-hidden">
            {searchable && (
              <div className="p-3 border-b border-slate-200">
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Search options..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            <div className="overflow-y-auto" style={{ maxHeight }}>
              {showSelectAll && availableOptions.length > 0 && (
                <div
                  className={`px-4 py-3 cursor-pointer transition-colors duration-150 flex items-center justify-between border-b border-slate-200 ${
                    allSelected
                      ? "bg-blue-50 text-blue-900 hover:bg-blue-100"
                      : "text-slate-900 hover:bg-slate-50"
                  }`}
                  onClick={handleSelectAll}
                >
                  <div className="flex-1">
                    <div className="font-medium text-sm">
                      {allSelected ? "Deselect All" : "Select All"}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {allSelected
                        ? `Deselect all ${availableOptions.length} options`
                        : `Select all ${availableOptions.length} options`}
                    </div>
                  </div>
                  {allSelected && <Check className="h-4 w-4 text-blue-600" />}
                </div>
              )}

              {filteredOptions.length > 0 ? (
                filteredOptions.map((option) => (
                  <div
                    key={option.value}
                    className={`px-4 py-3 cursor-pointer transition-colors duration-150 flex items-center justify-between ${
                      option.disabled
                        ? "text-slate-400 cursor-not-allowed bg-slate-50"
                        : selectedValues.includes(option.value)
                        ? "bg-blue-50 text-blue-900 hover:bg-blue-100"
                        : "text-slate-900 hover:bg-slate-50"
                    }`}
                    onClick={() =>
                      !option.disabled && toggleOption(option.value)
                    }
                  >
                    <div className="flex-1">
                      <div className="font-medium text-sm">{option.label}</div>
                      {option.description && (
                        <div className="text-xs text-slate-500 mt-1">
                          {option.description}
                        </div>
                      )}
                    </div>
                    {selectedValues.includes(option.value) && (
                      <Check className="h-4 w-4 text-blue-600" />
                    )}
                  </div>
                ))
              ) : (
                <div className="px-4 py-3 text-slate-500 text-sm text-center">
                  No options found
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600 flex items-center">
          <svg
            className="w-4 h-4 mr-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
};
