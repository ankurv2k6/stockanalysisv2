/**
 * Frontend Structured Logger
 *
 * Provides consistent logging format for frontend debugging and error tracking.
 * Logs are written to console in development and can be sent to backend in production.
 */

type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  component: string;
  message: string;
  context?: Record<string, unknown>;
  error_code?: string;
  user_action?: string;
}

interface LoggerOptions {
  sendToBackend?: boolean;
  backendUrl?: string;
}

const defaultOptions: LoggerOptions = {
  sendToBackend: false,
  backendUrl: '/api/logs',
};

class FrontendLogger {
  private component: string;
  private options: LoggerOptions;

  constructor(component: string, options: LoggerOptions = {}) {
    this.component = component;
    this.options = { ...defaultOptions, ...options };
  }

  private createEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>
  ): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      component: this.component,
      message,
      context,
      error_code: context?.error_code as string | undefined,
      user_action: context?.user_action as string | undefined,
    };
  }

  private formatForConsole(entry: LogEntry): string {
    const contextStr = entry.context
      ? ` | ${JSON.stringify(entry.context)}`
      : '';
    return `[${entry.timestamp}] [${entry.level}] [${entry.component}] ${entry.message}${contextStr}`;
  }

  private log(level: LogLevel, message: string, context?: Record<string, unknown>) {
    const entry = this.createEntry(level, message, context);
    const formatted = this.formatForConsole(entry);

    // Console output based on level
    switch (level) {
      case 'DEBUG':
        if (process.env.NODE_ENV === 'development') {
          console.debug(formatted);
        }
        break;
      case 'INFO':
        console.info(formatted);
        break;
      case 'WARN':
        console.warn(formatted);
        break;
      case 'ERROR':
        console.error(formatted);
        break;
    }

    // Send to backend in production if enabled
    if (
      this.options.sendToBackend &&
      process.env.NODE_ENV === 'production' &&
      level !== 'DEBUG'
    ) {
      this.sendToBackend(entry).catch(() => {
        // Silently fail - don't want logging to break the app
      });
    }

    return entry;
  }

  private async sendToBackend(entry: LogEntry): Promise<void> {
    try {
      await fetch(this.options.backendUrl!, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
      });
    } catch {
      // Fire and forget
    }
  }

  debug(message: string, context?: Record<string, unknown>) {
    return this.log('DEBUG', message, context);
  }

  info(message: string, context?: Record<string, unknown>) {
    return this.log('INFO', message, context);
  }

  warn(message: string, context?: Record<string, unknown>) {
    return this.log('WARN', message, context);
  }

  error(message: string, context?: Record<string, unknown>) {
    return this.log('ERROR', message, context);
  }

  // Convenience method for API errors
  apiError(
    endpoint: string,
    status: number,
    errorMessage: string,
    context?: Record<string, unknown>
  ) {
    return this.error('API request failed', {
      error_code: 'API_FETCH_ERROR',
      endpoint,
      status,
      errorMessage,
      ...context,
    });
  }

  // Convenience method for user actions
  userAction(action: string, context?: Record<string, unknown>) {
    return this.info('User action', {
      user_action: action,
      ...context,
    });
  }
}

// Factory function to create loggers
export function createLogger(
  component: string,
  options?: LoggerOptions
): FrontendLogger {
  return new FrontendLogger(component, options);
}

// Pre-configured loggers for common components
export const apiLogger = createLogger('api');
export const dashboardLogger = createLogger('dashboard');
export const companiesLogger = createLogger('companies');
export const adminLogger = createLogger('admin');

// Default export for simple usage
export default createLogger;
