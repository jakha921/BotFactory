/**
 * Rate limiter utility for controlling API call frequency
 * Provides debounce and throttle functions to prevent excessive API calls
 */

interface RateLimiterOptions {
  delay: number;
  maxCalls?: number;
  timeWindow?: number;
}

/**
 * Debounce function - delays execution until after the specified delay
 * @param fn - Function to debounce
 * @param delay - Delay in milliseconds
 * @returns Debounced function
 */
export const debounce = <T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delay);
  };
};

/**
 * Throttle function - limits function execution to once per specified time window
 * @param fn - Function to throttle
 * @param delay - Time window in milliseconds
 * @returns Throttled function
 */
export const throttle = <T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let lastCall = 0;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    const now = Date.now();
    const timeSinceLastCall = now - lastCall;

    if (timeSinceLastCall >= delay) {
      lastCall = now;
      fn(...args);
    } else {
      // Schedule call after remaining delay
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      const remainingDelay = delay - timeSinceLastCall;
      timeoutId = setTimeout(() => {
        lastCall = Date.now();
        fn(...args);
        timeoutId = null;
      }, remainingDelay);
    }
  };
};

/**
 * Rate limiter class for more advanced rate limiting
 */
export class RateLimiter {
  private callHistory: number[] = [];
  private readonly delay: number;
  private readonly maxCalls: number;
  private readonly timeWindow: number;

  constructor(options: RateLimiterOptions) {
    this.delay = options.delay;
    this.maxCalls = options.maxCalls ?? 10;
    this.timeWindow = options.timeWindow ?? 60000; // 1 minute default
  }

  /**
   * Check if a call can be made based on rate limit
   * @returns true if call is allowed, false otherwise
   */
  canCall(): boolean {
    const now = Date.now();

    // Remove old entries outside the time window
    this.callHistory = this.callHistory.filter((timestamp) => now - timestamp < this.timeWindow);

    // Check if we're under the limit
    return this.callHistory.length < this.maxCalls;
  }

  /**
   * Record a call
   */
  recordCall(): void {
    this.callHistory.push(Date.now());
  }

  /**
   * Execute function with rate limiting
   * @param fn - Function to execute
   * @returns Promise that resolves when function is executed or rejects if rate limited
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // delay is stored in this.delay for future use
    if (!this.canCall()) {
      throw new Error(
        `Rate limit exceeded. Maximum ${this.maxCalls} calls per ${this.timeWindow}ms`
      );
    }

    this.recordCall();
    return fn();
  }

  /**
   * Get time until next call is allowed (in milliseconds)
   * @returns milliseconds until next call is allowed, 0 if allowed now
   */
  getTimeUntilNextCall(): number {
    if (this.canCall()) {
      return 0;
    }

    const now = Date.now();
    const oldestCall = Math.min(...this.callHistory);
    const timeSinceOldest = now - oldestCall;

    return Math.max(0, this.timeWindow - timeSinceOldest);
  }

  /**
   * Reset rate limiter
   */
  reset(): void {
    this.callHistory = [];
  }
}
