# Documentation

Detailed documentation for the OpenRouter LLM Console project.

## Organization

This directory contains in-depth documentation for specific features, implementations, and security topics. For general project information and setup, see the [main README](../README.md).

### Features (`features/`)

Detailed documentation for major features:

- **[Search Feature](features/search.md)** - Full-text search with SQLite FTS5, advanced query syntax, and filtering
- **[Caching](features/caching.md)** - In-memory caching implementation for profiles and models
- **[Error Handling](features/error-handling.md)** - Comprehensive streaming error handling infrastructure
- **[Structured Errors](features/structured-errors.md)** - Machine-readable error codes and standardized responses

### Security (`security/`)

Security-related documentation:

- **[Path Traversal Fix](security/path-traversal-fix.md)** - Details of the path traversal vulnerability and its resolution

## Backend Documentation

Backend-specific documentation is located in the `backend/` directory:

- **[Backend README](../backend/README.md)** - Complete backend architecture and development guide
- **[Rate Limiting](../backend/RATE_LIMITING.md)** - Comprehensive rate limiting configuration and usage
- **[Database Migrations](../backend/migrations/README.md)** - Migration system documentation

## Testing Documentation

Comprehensive testing guides:

- **[Testing Guide](../TESTING_GUIDE.md)** - Complete testing documentation for frontend and backend
- **[Testing Quick Reference](../TESTING_QUICK_REFERENCE.md)** - Quick command reference
- **[Frontend Tests README](../frontend/tests/README.md)** - Frontend test suite documentation

## Project Information

- **[Changelog](../CHANGELOG.md)** - Complete project history and feature implementations
- **[Main README](../README.md)** - Project overview, setup instructions, and API reference

## For Developers

If you're contributing to the project or want to understand the architecture:

1. Start with the [Main README](../README.md) for project overview and setup
2. Read the [Backend README](../backend/README.md) for architecture details
3. Check specific feature docs in `features/` for implementation details
4. Review [Testing Guide](../TESTING_GUIDE.md) before making changes
5. Consult the [Changelog](../CHANGELOG.md) to understand recent changes

## Quick Links

**Getting Started:**
- [Setup Instructions](../README.md#setup)
- [Prerequisites](../README.md#prerequisites)
- [Environment Configuration](../backend/README.md#environment-variables)

**Development:**
- [Running Locally](../README.md#setup)
- [Testing](../TESTING_GUIDE.md)
- [Contributing](../README.md#contributing)

**API Reference:**
- [API Endpoints](../README.md#api-reference)
- [Streaming](../README.md#streaming)
- [Rate Limiting](../backend/RATE_LIMITING.md)
