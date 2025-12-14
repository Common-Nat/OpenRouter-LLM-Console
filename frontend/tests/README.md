# Frontend Tests

Comprehensive test suite for frontend logger service and React components.

## Setup

### Prerequisites
- Node.js 18+ installed
- npm installed

### Installation

**Option 1: Run installation script (Windows)**
```powershell
cd frontend
.\install-tests.ps1
```

**Option 2: Manual installation**
```bash
cd frontend
npm install
```

## Running Tests

### All Tests
```bash
npm test              # Run all tests once
```

### Watch Mode (Recommended for Development)
```bash
npm run test:watch    # Re-runs tests on file changes
```

### Visual UI
```bash
npm run test:ui       # Opens interactive test UI in browser
```

### Coverage Report
```bash
npm run test:coverage # Generates coverage report
# Opens in: coverage/index.html
```

## Test Files

### `tests/logger.test.js`
Unit tests for the frontend logging service.

**What it tests:**
- ✅ Session ID generation and persistence
- ✅ Data sanitization (API keys, tokens, passwords)
- ✅ Log level filtering (dev vs production)
- ✅ Batch queuing with size limits
- ✅ Backend communication via fetch
- ✅ Rate limiting handling (429 responses)
- ✅ Exponential backoff retry logic
- ✅ localStorage persistence
- ✅ sendBeacon synchronous flush
- ✅ Context enrichment

**Run specific tests:**
```bash
npm test logger.test.js
npm test -- -t "should redact sensitive"  # Filter by test name
```

### `tests/ErrorBoundary.test.jsx`
Integration tests for React error boundary component.

**What it tests:**
- ✅ Error catching from child components
- ✅ Fallback UI rendering
- ✅ Logger integration (componentError)
- ✅ Custom context passing
- ✅ Recovery actions (Try Again, Reload)
- ✅ GitHub issue link generation
- ✅ Development mode details
- ✅ Nested boundaries

**Run specific tests:**
```bash
npm test ErrorBoundary.test.jsx
npm test -- -t "should catch errors"
```

## Test Configuration

### `vitest.config.js`
Vitest configuration with jsdom environment and coverage settings.

### `tests/setup.js`
Global test setup:
- Mocks localStorage
- Mocks sessionStorage
- Mocks fetch
- Mocks sendBeacon
- Imports @testing-library/jest-dom for matchers
- Configures cleanup after each test

## Writing New Tests

### Unit Test Example
```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import myModule from '../src/myModule.js';

describe('MyModule', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should do something', () => {
    const result = myModule.doSomething();
    expect(result).toBe(true);
  });
});
```

### Component Test Example
```javascript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MyComponent from '../src/components/MyComponent.jsx';

describe('MyComponent', () => {
  it('should handle click', async () => {
    const user = userEvent.setup();
    render(<MyComponent />);
    
    const button = screen.getByRole('button', { name: /click me/i });
    await user.click(button);
    
    expect(screen.getByText('Clicked!')).toBeInTheDocument();
  });
});
```

## Troubleshooting

### Tests not running
```bash
# Clear cache
rm -rf node_modules coverage .vite
npm install
```

### Mock issues
Check `tests/setup.js` - all mocks should be configured there.

### Import errors
Ensure `vitest.config.js` has correct path aliases:
```javascript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
},
```

### Coverage not generated
Make sure you have write permissions in the `frontend/` directory.

## Coverage Goals

Current coverage (target):
- **logger.js**: 95%+ (all critical paths)
- **ErrorBoundary.jsx**: 90%+ (all user paths)
- **Overall frontend**: 80%+

## CI/CD Integration

Add to `.github/workflows/test.yml`:
```yaml
frontend-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-node@v3
      with:
        node-version: 18
    - run: cd frontend && npm ci
    - run: cd frontend && npm test
    - run: cd frontend && npm run test:coverage
    - uses: actions/upload-artifact@v3
      with:
        name: coverage
        path: frontend/coverage
```

## Next Steps

**Recommended additions:**
1. Add tests for tab components (ChatTab, CodeTab, etc.)
2. Add tests for utils/errorHandling.js
3. Add tests for api/client.js
4. Add E2E tests with Playwright
5. Add visual regression tests
