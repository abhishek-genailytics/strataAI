/**
 * Client-side error logging service for StrataAI.
 */
import { ErrorInfo } from 'react';

export interface ClientErrorLog {
  error: Error;
  errorInfo?: ErrorInfo;
  timestamp: string;
  userAgent: string;
  url: string;
  userId: string | null;
  additionalContext?: Record<string, any>;
}

export interface ApiErrorLog {
  message: string;
  status: number;
  endpoint: string;
  method: string;
  timestamp: string;
  userId: string | null;
  requestId?: string;
  responseData?: any;
}

class ErrorLoggingService {
  private readonly maxRetries = 3;
  private readonly retryDelay = 1000;

  /**
   * Log a client-side error (React errors, JavaScript errors, etc.)
   */
  async logClientError(errorLog: ClientErrorLog): Promise<string> {
    const errorId = this.generateErrorId();
    
    try {
      // Prepare error data for logging
      const errorData = {
        id: errorId,
        type: 'client_error',
        message: errorLog.error.message,
        stack: errorLog.error.stack,
        componentStack: errorLog.errorInfo?.componentStack,
        timestamp: errorLog.timestamp,
        userAgent: errorLog.userAgent,
        url: errorLog.url,
        userId: errorLog.userId,
        additionalContext: errorLog.additionalContext,
      };

      // Log to console for development
      if (process.env.NODE_ENV === 'development') {
        console.group(`🚨 Client Error [${errorId}]`);
        console.error('Error:', errorLog.error);
        console.error('Error Info:', errorLog.errorInfo);
        console.error('Context:', errorData);
        console.groupEnd();
      }

      // Send to backend error logging endpoint
      await this.sendErrorToBackend('/api/errors/client', errorData);

      // Store in local storage as backup
      this.storeErrorLocally(errorData);

      return errorId;
    } catch (loggingError) {
      console.error('Failed to log client error:', loggingError);
      // Still store locally even if backend fails
      this.storeErrorLocally({
        id: errorId,
        type: 'client_error',
        message: errorLog.error.message,
        timestamp: errorLog.timestamp,
        failed_to_send: true,
      });
      return errorId;
    }
  }

  /**
   * Log an API error (HTTP errors, network failures, etc.)
   */
  async logApiError(errorLog: ApiErrorLog): Promise<string> {
    const errorId = this.generateErrorId();
    
    try {
      const errorData = {
        id: errorId,
        type: 'api_error',
        message: errorLog.message,
        status: errorLog.status,
        endpoint: errorLog.endpoint,
        method: errorLog.method,
        timestamp: errorLog.timestamp,
        userId: errorLog.userId,
        requestId: errorLog.requestId,
        responseData: errorLog.responseData,
      };

      // Log to console for development
      if (process.env.NODE_ENV === 'development') {
        console.group(`🔥 API Error [${errorId}]`);
        console.error(`${errorLog.method} ${errorLog.endpoint} - ${errorLog.status}`);
        console.error('Message:', errorLog.message);
        console.error('Response:', errorLog.responseData);
        console.groupEnd();
      }

      // Send to backend
      await this.sendErrorToBackend('/api/errors/api', errorData);

      // Store locally
      this.storeErrorLocally(errorData);

      return errorId;
    } catch (loggingError) {
      console.error('Failed to log API error:', loggingError);
      return errorId;
    }
  }

  /**
   * Log a user action error (form validation, user input errors, etc.)
   */
  async logUserError(message: string, context?: Record<string, any>): Promise<string> {
    const errorId = this.generateErrorId();
    
    try {
      const errorData = {
        id: errorId,
        type: 'user_error',
        message,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userId: this.getCurrentUserId(),
        context,
      };

      // Only log to backend for user errors, not console (too noisy)
      await this.sendErrorToBackend('/api/errors/user', errorData);

      return errorId;
    } catch (loggingError) {
      console.error('Failed to log user error:', loggingError);
      return errorId;
    }
  }

  /**
   * Get error statistics for the current user
   */
  async getErrorStatistics(): Promise<any> {
    try {
      const response = await fetch('/api/errors/statistics', {
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch error statistics: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch error statistics:', error);
      return null;
    }
  }

  /**
   * Send error data to backend with retry logic
   */
  private async sendErrorToBackend(endpoint: string, errorData: any): Promise<void> {
    let lastError: Error | null = null;
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...this.getAuthHeaders(),
          },
          body: JSON.stringify(errorData),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Success - exit retry loop
        return;
      } catch (error) {
        lastError = error as Error;
        
        if (attempt < this.maxRetries) {
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
        }
      }
    }

    // All retries failed
    throw lastError;
  }

  /**
   * Store error data in local storage as backup
   */
  private storeErrorLocally(errorData: any): void {
    try {
      const key = `error_log_${Date.now()}`;
      const existingLogs = this.getLocalErrorLogs();
      
      // Limit local storage to last 50 errors
      const logs = [...existingLogs, { key, data: errorData }].slice(-50);
      
      localStorage.setItem('strata_ai_error_logs', JSON.stringify(logs));
    } catch (error) {
      console.error('Failed to store error locally:', error);
    }
  }

  /**
   * Get locally stored error logs
   */
  private getLocalErrorLogs(): Array<{ key: string; data: any }> {
    try {
      const logs = localStorage.getItem('strata_ai_error_logs');
      return logs ? JSON.parse(logs) : [];
    } catch {
      return [];
    }
  }

  /**
   * Clear local error logs
   */
  clearLocalErrorLogs(): void {
    try {
      localStorage.removeItem('strata_ai_error_logs');
    } catch (error) {
      console.error('Failed to clear local error logs:', error);
    }
  }

  /**
   * Generate unique error ID
   */
  private generateErrorId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current user ID from auth context
   */
  private getCurrentUserId(): string | null {
    try {
      const authData = localStorage.getItem('auth');
      if (authData) {
        const parsed = JSON.parse(authData);
        return parsed.user?.id || null;
      }
    } catch {
      // Ignore parsing errors
    }
    return null;
  }

  /**
   * Get authentication headers for API requests
   */
  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {};
    
    try {
      const authData = localStorage.getItem('auth');
      if (authData) {
        const parsed = JSON.parse(authData);
        if (parsed.token) {
          headers['Authorization'] = `Bearer ${parsed.token}`;
        }
      }
    } catch {
      // Ignore auth errors
    }
    
    return headers;
  }
}

// Export singleton instance
export const errorLoggingService = new ErrorLoggingService();
