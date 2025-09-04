import React from "react";
import { PasswordStrength } from "../../utils/validation";

interface PasswordStrengthIndicatorProps {
  strength: PasswordStrength;
  className?: string;
}

export const PasswordStrengthIndicator: React.FC<
  PasswordStrengthIndicatorProps
> = ({ strength, className = "" }) => {
  const getStrengthColor = (score: number) => {
    switch (score) {
      case 0:
      case 1:
        return "bg-red-500";
      case 2:
        return "bg-orange-500";
      case 3:
        return "bg-yellow-500";
      case 4:
        return "bg-green-500";
      default:
        return "bg-gray-300";
    }
  };

  const getStrengthText = (score: number) => {
    switch (score) {
      case 0:
      case 1:
        return "Very weak";
      case 2:
        return "Weak";
      case 3:
        return "Fair";
      case 4:
        return "Strong";
      default:
        return "";
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Strength bars */}
      <div className="flex space-x-1">
        {[1, 2, 3, 4].map((level) => (
          <div
            key={level}
            className={`h-2 flex-1 rounded-full transition-colors duration-200 ${
              level <= strength.score
                ? getStrengthColor(strength.score)
                : "bg-gray-200"
            }`}
          />
        ))}
      </div>

      {/* Strength text */}
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-600">
          Password strength: {getStrengthText(strength.score)}
        </span>
        {strength.isValid && (
          <span className="text-sm text-green-600">✓ Strong enough</span>
        )}
      </div>

      {/* Feedback */}
      {strength.feedback.length > 0 && (
        <ul className="text-xs text-gray-500 space-y-1">
          {strength.feedback.map((feedback: string, index: number) => (
            <li key={index} className="flex items-center">
              <span className="mr-1">•</span>
              {feedback}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
