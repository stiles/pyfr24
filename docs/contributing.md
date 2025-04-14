# Contributing

Thank you for your interest in contributing to Pyfr24! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/your-username/pyfr24.git
cd pyfr24
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Running Tests

The package includes a comprehensive test suite. To run the tests:

```bash
python run_tests.py
```

## Code Style

We follow PEP 8 guidelines with some modifications:
- Line length limit: 100 characters
- Use double quotes for strings
- Use trailing commas in multi-line structures

## Pull Request Process

1. Create a new branch for your feature:
```bash
git checkout -b feature-name
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "Description of changes"
```

3. Push to your fork:
```bash
git push origin feature-name
```

4. Open a Pull Request with:
   - Clear description of changes
   - Any relevant issue numbers
   - Screenshots for UI changes
   - Test coverage for new features

## Documentation

When adding new features, please include:
- Docstrings for new functions/methods
- Updates to relevant documentation files
- Example usage in docstrings
- Updates to the README if needed

## Testing Guidelines

- Write tests for new features
- Maintain or improve test coverage
- Include both unit and integration tests
- Mock external API calls in tests

## Reporting Issues

When reporting issues, please include:
- Python version
- Pyfr24 version
- Operating system
- Minimal reproducible example
- Expected vs actual behavior
- Any relevant error messages

## Feature Requests

For feature requests, please:
- Check existing issues first
- Describe the feature clearly
- Explain the use case
- Provide example usage if possible

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## License

By contributing, you agree that your contributions will be licensed under the MIT License. 