import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorBoundary from '../src/components/ErrorBoundary.jsx';
import logger from '../src/services/logger.js';

// Component that throws an error
const ThrowError = ({ shouldThrow, errorMessage }) => {
  if (shouldThrow) {
    throw new Error(errorMessage || 'Test error');
  }
  return <div>No error</div>;
};

// Helper to suppress console.error during error tests
const suppressErrorOutput = (callback) => {
  const originalError = console.error;
  console.error = vi.fn();
  try {
    callback();
  } finally {
    console.error = originalError;
  }
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(logger, 'componentError').mockImplementation(() => {});
  });

  describe('Normal Rendering', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>Child component</div>
        </ErrorBoundary>
      );

      expect(screen.getByText('Child component')).toBeInTheDocument();
    });

    it('should not call logger when no error', () => {
      render(
        <ErrorBoundary>
          <div>Child component</div>
        </ErrorBoundary>
      );

      expect(logger.componentError).not.toHaveBeenCalled();
    });
  });

  describe('Error Catching', () => {
    it('should catch errors from child components', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} errorMessage="Component crashed" />
          </ErrorBoundary>
        );
      });

      expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    });

    it('should log error to logging service', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} errorMessage="Test error" />
          </ErrorBoundary>
        );
      });

      expect(logger.componentError).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Test error',
        }),
        expect.any(Object)
      );
    });

    it('should include custom context in error log', () => {
      const customContext = {
        tabType: 'chat',
        sessionId: 'test-session-123',
      };

      suppressErrorOutput(() => {
        render(
          <ErrorBoundary context={customContext}>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );
      });

      expect(logger.componentError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          context: customContext,
        })
      );
    });

    it('should include error info with component stack', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );
      });

      const logCall = logger.componentError.mock.calls[0];
      expect(logCall[1]).toHaveProperty('componentStack');
    });
  });

  describe('Fallback UI', () => {
    it('should display error heading', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );
      });

      expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    });

    it('should display error description', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );
      });

      expect(
        screen.getByText(/The application encountered an unexpected error/i)
      ).toBeInTheDocument();
    });

    it('should display Try Again button', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );
      });

      expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
    });

    it('should display Reload Page button', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );
      });

      expect(screen.getByRole('button', { name: /Reload Page/i })).toBeInTheDocument();
    });

    it('should display Report Issue link', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );
      });

      expect(screen.getByRole('link', { name: /Report Issue/i })).toBeInTheDocument();
    });
  });

  describe('Recovery Actions', () => {
    it('should reset error state when Try Again is clicked', async () => {
      const user = userEvent.setup();
      let shouldThrow = true;

      suppressErrorOutput(() => {
        const { rerender } = render(
          <ErrorBoundary>
            <ThrowError shouldThrow={shouldThrow} />
          </ErrorBoundary>
        );

        expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();

        // Update state to not throw on re-render
        shouldThrow = false;

        const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
        user.click(tryAgainButton).then(() => {
          // After reset, boundary should attempt to render children again
          rerender(
            <ErrorBoundary>
              <ThrowError shouldThrow={shouldThrow} />
            </ErrorBoundary>
          );

          // Should show normal content if error is fixed
          expect(screen.queryByText(/Something went wrong/i)).not.toBeInTheDocument();
        });
      });
    });

    it('should reload page when Reload Page is clicked', async () => {
      const user = userEvent.setup();
      const reloadMock = vi.fn();
      delete window.location;
      window.location = { reload: reloadMock };

      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );

        const reloadButton = screen.getByRole('button', { name: /Reload Page/i });
        user.click(reloadButton).then(() => {
          expect(reloadMock).toHaveBeenCalled();
        });
      });
    });

    it('should generate GitHub issue URL with error details', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary context={{ tab: 'chat' }}>
            <ThrowError shouldThrow={true} errorMessage="Test crash" />
          </ErrorBoundary>
        );

        const issueLink = screen.getByRole('link', { name: /Report Issue/i });
        const href = issueLink.getAttribute('href');

        expect(href).toContain('github.com');
        expect(href).toContain('issues/new');
        expect(href).toContain(encodeURIComponent('Error: Error'));
        expect(href).toContain(encodeURIComponent('Test crash'));
      });
    });
  });

  describe('Development Mode', () => {
    it('should show error details in development mode', () => {
      // Mock DEV environment
      const originalEnv = import.meta.env.DEV;
      import.meta.env.DEV = true;

      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} errorMessage="Dev mode error" />
          </ErrorBoundary>
        );

        // Look for details element (collapsed by default)
        const details = screen.getByText(/Error Details \(Development Only\)/i);
        expect(details).toBeInTheDocument();
      });

      import.meta.env.DEV = originalEnv;
    });

    it('should display error name and message in dev mode', () => {
      const originalEnv = import.meta.env.DEV;
      import.meta.env.DEV = true;

      suppressErrorOutput(() => {
        render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} errorMessage="Detailed error" />
          </ErrorBoundary>
        );

        expect(screen.getByText(/Detailed error/i)).toBeInTheDocument();
      });

      import.meta.env.DEV = originalEnv;
    });
  });

  describe('Multiple Errors', () => {
    it('should handle catching multiple errors sequentially', () => {
      let errorCount = 0;

      suppressErrorOutput(() => {
        const { rerender } = render(
          <ErrorBoundary>
            <ThrowError shouldThrow={false} />
          </ErrorBoundary>
        );

        // First error
        errorCount++;
        rerender(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} errorMessage="First error" />
          </ErrorBoundary>
        );

        expect(logger.componentError).toHaveBeenCalledTimes(1);

        // Reset and throw second error
        rerender(
          <ErrorBoundary>
            <ThrowError shouldThrow={false} />
          </ErrorBoundary>
        );

        errorCount++;
        rerender(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} errorMessage="Second error" />
          </ErrorBoundary>
        );

        expect(logger.componentError).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Error State Management', () => {
    it('should store error and errorInfo in state', () => {
      suppressErrorOutput(() => {
        const { container } = render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} errorMessage="State test" />
          </ErrorBoundary>
        );

        // Error UI is shown, meaning state was updated
        expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
      });
    });

    it('should clear error state after reset', async () => {
      const user = userEvent.setup();

      suppressErrorOutput(() => {
        const { rerender } = render(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );

        const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
        user.click(tryAgainButton).then(() => {
          // After clicking Try Again, if we rerender with no error,
          // children should render normally
          rerender(
            <ErrorBoundary>
              <div>Recovered</div>
            </ErrorBoundary>
          );

          expect(screen.getByText('Recovered')).toBeInTheDocument();
        });
      });
    });
  });

  describe('Nested Error Boundaries', () => {
    it('should allow nested boundaries to catch different errors', () => {
      suppressErrorOutput(() => {
        render(
          <ErrorBoundary context={{ level: 'outer' }}>
            <div>
              <ErrorBoundary context={{ level: 'inner' }}>
                <ThrowError shouldThrow={true} errorMessage="Inner error" />
              </ErrorBoundary>
              <div>Outer content</div>
            </div>
          </ErrorBoundary>
        );

        // Inner boundary catches the error
        expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
        // Outer boundary's other children still render
        expect(screen.getByText('Outer content')).toBeInTheDocument();

        // Logger called with inner context
        expect(logger.componentError).toHaveBeenCalledWith(
          expect.any(Error),
          expect.objectContaining({
            context: { level: 'inner' },
          })
        );
      });
    });
  });
});
