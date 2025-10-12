# Contributing to ClamAV GUI

Thank you for considering contributing to ClamAV GUI! We welcome all contributions, whether they're bug reports, feature requests, documentation improvements, or code contributions.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Style and Standards](#code-style-and-standards)
4. [Testing](#testing)
5. [Submitting Changes](#submitting-changes)
6. [Reporting Issues](#reporting-issues)
7. [Feature Requests](#feature-requests)

## Getting Started

### Prerequisites

Before you begin contributing, ensure you have:

- **Python 3.10+**: For running and developing the application
- **Git**: For version control
- **ClamAV**: For testing antivirus functionality (optional for development)
- **Virtual Environment**: Recommended for development

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** to your local machine:
   ```bash
   git clone https://github.com/YOUR_USERNAME/clamav-gui.git
   cd clamav-gui
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/Nsfr750/clamav-gui.git
   ```
4. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/description-of-fix
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Verify Installation

```bash
# Test that the application runs
python -m clamav_gui --help

# Run tests
python -m pytest --version
```

### 4. Development Tools Setup

```bash
# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# Install code formatting tools
pip install black isort mypy
```

## Code Style and Standards

### Python Standards

- **PEP 8 Compliance**: Follow Python Enhancement Proposal 8 guidelines
- **Type Hints**: Use type annotations for all functions and methods
- **Docstrings**: Write comprehensive docstrings for all public APIs
- **Imports**: Organize imports following PEP 8 (standard library, third-party, local)

### Code Organization

- **Small Functions**: Keep functions focused and under 50 lines when possible
- **Clear Naming**: Use descriptive names for variables, functions, and classes
- **Error Handling**: Implement proper exception handling with meaningful messages
- **Logging**: Use appropriate logging levels (DEBUG, INFO, WARNING, ERROR)

### GUI Development

- **PySide6 Best Practices**: Follow Qt design patterns and guidelines
- **Responsive Design**: Ensure UI works across different screen sizes
- **Accessibility**: Include proper labels and keyboard navigation
- **Internationalization**: Use the translation system for all user-facing text

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=clamav_gui

# Run specific test categories
python -m pytest -m unit          # Unit tests
python -m pytest -m integration   # Integration tests
python -m pytest -m gui           # GUI tests
python -m pytest -m performance   # Performance tests

# Run tests with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_lang_manager.py
```

### Writing Tests

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test how components work together
- **GUI Tests**: Use `pytest-qt` for testing PySide6 components
- **Mocking**: Use mocks for external dependencies (ClamAV, file system, etc.)

### Test Structure

```
tests/
├── test_unit_*.py          # Unit tests
├── test_integration_*.py   # Integration tests
├── test_gui_*.py          # GUI component tests
└── conftest.py            # Test fixtures and configuration
```

## Submitting Changes

### Branch Naming Convention

```bash
# Feature branches
feature/feature-name
feature/add-scheduled-scans

# Bug fix branches
bugfix/fix-crash-on-scan
bugfix/update-dependencies

# Documentation branches
docs/update-user-guide
docs/fix-typos
```

### Commit Guidelines

- **Clear Messages**: Use imperative mood ("Add feature" not "Added feature")
- **Atomic Commits**: Each commit should represent one logical change
- **Reference Issues**: Include issue numbers when applicable (#123)

Example commit messages:
```
feat: Add scheduled scan functionality

- Implement daily/weekly scan scheduling
- Add settings UI for scan intervals
- Update documentation

Closes #45
```

### Pull Request Process

1. **Create a Branch**: Work on a feature branch, not main
2. **Make Changes**: Implement your feature or fix
3. **Add Tests**: Include tests for new functionality
4. **Update Documentation**: Update docs if needed
5. **Run Tests**: Ensure all tests pass
6. **Submit PR**: Create a pull request against the main branch

### Pull Request Template

When submitting a PR, please include:

- **Description**: What the PR does and why it's needed
- **Changes**: Summary of what was changed
- **Testing**: How the changes were tested
- **Screenshots**: If the PR affects the UI
- **Related Issues**: Links to related issues or discussions

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Steps to Reproduce**: Clear, numbered steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, ClamAV version
- **Error Messages**: Any error output or logs
- **Screenshots**: If applicable

### Issue Template

```markdown
## Bug Report

### Description
[Brief description of the bug]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Environment
- OS: [Windows/Linux/Mac]
- Python: [3.10, 3.11, etc.]
- ClamAV GUI Version: [1.1.0]
- ClamAV Version: [1.0.0]

### Additional Information
[Any other relevant details]
```

## Feature Requests

### Suggesting Features

When suggesting new features:

- **Use Case**: Explain why this feature is needed
- **Alternatives**: Mention any existing alternatives
- **Implementation**: If you have ideas about implementation
- **Priority**: How important is this feature?

### Feature Request Template

```markdown
## Feature Request

### Description
[Clear description of the feature]

### Use Case
[Why is this feature needed?]

### Proposed Solution
[How should this feature work?]

### Alternatives Considered
[Other solutions you've considered]

### Additional Context
[Any other relevant information]
```

## Development Workflow

### Before Starting Work

1. **Check Existing Issues**: See if someone is already working on it
2. **Create an Issue**: For larger features, create an issue first
3. **Assign Yourself**: If you're working on it, assign yourself to the issue

### During Development

1. **Keep Branches Updated**: Regularly merge/rebase from upstream main
2. **Write Tests**: Test-driven development is encouraged
3. **Update Documentation**: Keep docs in sync with code changes
4. **Code Review**: Submit PRs for review before merging

### After Development

1. **Test Thoroughly**: Ensure all tests pass
2. **Update CHANGELOG**: Add entry for your changes
3. **Clean Up**: Remove any temporary files or debugging code

## Community Guidelines

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Collaborative**: Work together to achieve common goals
- **Be Patient**: Understand that maintainers are volunteers
- **Be Helpful**: Help others when you can

## Recognition

Contributors who make significant contributions may be:

- **Mentioned in Release Notes**: For major contributions
- **Added to Contributors List**: In README.md
- **Given Commit Access**: For trusted contributors

## Questions?

If you have questions about contributing:

- **Check Documentation**: Start with the docs in the `docs/` folder
- **Search Issues**: Someone may have asked the same question
- **Ask in Discussions**: Use GitHub Discussions for questions
- **Contact Maintainers**: For private questions, contact [nsfr750@yandex.com](mailto:nsfr750@yandex.com)

---

Thank you for contributing to ClamAV GUI! Your help makes the project better for everyone. 🎉
