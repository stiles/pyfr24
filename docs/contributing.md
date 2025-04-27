# Contributing

Thank you for your interest in contributing to Pyfr24. This document provides guidelines for contributing to the project.

## Development setup

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

## Running tests

Run the test suite:

```bash
python run_tests.py
```

## Code style

We follow PEP 8 guidelines with these modifications:

- Line length limit: 100 characters
- Use double quotes for strings
- Use trailing commas in multi-line structures

## Pull request process

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
   - Description of changes
   - Relevant issue numbers
   - Screenshots for UI changes
   - Tests for new features

## Documentation

When adding new features, include:

- Docstrings for new functions/methods
- Updates to documentation files
- Example usage in docstrings
- README updates if needed

## Testing guidelines

- Write tests for new features
- Maintain test coverage
- Include unit and integration tests
- Mock external API calls in tests

## Reporting issues

When reporting issues, include:

- Python version
- Pyfr24 version
- Operating system
- Reproducible example
- Expected vs actual behavior
- Error messages

## Feature requests

For feature requests:

- Check existing issues first
- Describe the feature
- Explain the use case
- Provide example usage

## Code of conduct

This project follows a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating you agree to its terms.

## License

By contributing, you agree to license your contributions under the MIT License.