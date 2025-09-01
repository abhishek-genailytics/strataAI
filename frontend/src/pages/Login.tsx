import React, { useState, useEffect } from "react";
import { Link, useLocation, Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Button, Input, Card } from "../components/ui";
import {
  validateEmail,
  validatePassword,
  validateForm,
} from "../utils/validation";

/**
 * Safely validates and normalizes a path for internal redirects.
 * Only allows paths starting with a single '/' and containing no scheme/host.
 * Falls back to defaultPath if validation fails.
 */
const getSafePath = (candidate: unknown, defaultPath: string = "/"): string => {
  // If not a string, return default
  if (typeof candidate !== "string") {
    return defaultPath;
  }

  // Normalize by trimming and ensuring it starts with a single '/'
  let path = candidate.trim();

  // Reject empty strings or paths not starting with '/'
  if (!path || !path.startsWith("/")) {
    return defaultPath;
  }

  // Remove any duplicate leading slashes
  path = path.replace(/^\/+/, "/");

  // Reject URLs with schemes (e.g., http:, https:, //, etc.)
  if (path.startsWith("//") || /^[a-z]+:/.test(path)) {
    return defaultPath;
  }

  // Reject URLs with host/colon before first slash
  if (path.includes(":")) {
    return defaultPath;
  }

  return path || defaultPath;
};

export const Login: React.FC = () => {
  const { signIn, user, loading } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Safely get and validate the redirect path
  const from = getSafePath(location.state?.from?.pathname, "/dashboard");

  // Real-time validation
  useEffect(() => {
    const validators = {
      email: validateEmail,
      password: validatePassword,
    };

    const { errors } = validateForm({ email, password }, validators);

    // Only show errors for touched fields
    const touchedErrors: Record<string, string> = {};
    Object.keys(errors).forEach((field) => {
      if (touched[field]) {
        touchedErrors[field] = errors[field];
      }
    });

    setFieldErrors(touchedErrors);
  }, [email, password, touched]);

  const handleFieldBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    // Mark all fields as touched for validation
    setTouched({ email: true, password: true });

    // Validate form
    const validators = {
      email: validateEmail,
      password: validatePassword,
    };

    const { isValid, errors } = validateForm({ email, password }, validators);

    if (!isValid) {
      setFieldErrors(errors);
      setIsLoading(false);
      return;
    }

    const result = await signIn(email, password);

    if (result.error) {
      setError(result.error);
    }

    setIsLoading(false);
  };

  if (user) {
    return <Navigate to={from} replace />;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to StrataAI
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your unified AI API gateway
          </p>
        </div>

        <Card>
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            <Input
              label="Email address"
              type="email"
              value={email}
              onChange={setEmail}
              onBlur={() => handleFieldBlur("email")}
              error={fieldErrors.email}
              required
              placeholder="Enter your email"
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
              onBlur={() => handleFieldBlur("password")}
              error={fieldErrors.password}
              required
              placeholder="Enter your password"
            />

            <Button type="submit" loading={isLoading} className="w-full">
              Sign in
            </Button>
          </form>

          <div className="mt-6 text-center space-y-3">
            <p className="text-sm text-gray-600">
              <Link
                to="/forgot-password"
                className="font-medium text-primary-600 hover:text-primary-500"
              >
                Forgot your password?
              </Link>
            </p>
            <p className="text-sm text-gray-600">
              Don't have an account?{" "}
              <Link
                to="/register"
                className="font-medium text-primary-600 hover:text-primary-500"
              >
                Sign up
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
