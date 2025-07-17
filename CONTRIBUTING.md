# Contributing to Autonomous DevOps Responder

Thank you for your interest in contributing to the Autonomous DevOps Responder! We welcome contributions from developers of all skill levels and backgrounds. This document provides guidelines and information for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8 or higher
- Git
- A GitHub account
- Basic understanding of DevOps concepts

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Autonomous-Devops-Responder.git
   cd Autonomous-Devops-Responder
   ```

3. **Add the upstream repository** as a remote:
   ```bash
   git remote add upstream https://github.com/intekhab1025/Autonomous-Devops-Responder.git
   ```

4. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

5. **Run the test suite** to ensure everything is working:
   ```bash
   pytest
   ```

## How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **🐛 Bug Reports**: Help us identify and fix issues
- **✨ Feature Requests**: Suggest new features or improvements
- **📝 Documentation**: Improve or add documentation
- **🧪 Tests**: Add or improve test coverage
- **💻 Code**: Implement new features or fix bugs
- **🎨 Design**: Improve user interface and experience
- **🌍 Translations**: Help make the project accessible globally

### Finding Ways to Contribute

- Check our [issue tracker](https://github.com/intekhab1025/Autonomous-Devops-Responder/issues) for open issues
- Look for issues labeled `good first issue` for beginner-friendly tasks
- Check issues labeled `help wanted` for areas where we need assistance
- Review our [roadmap](README.md#roadmap) for planned features

## Development Workflow

### Branch Naming Convention

Use descriptive branch names with prefixes:
- `feature/` for new features (e.g., `feature/slack-integration`)
- `bugfix/` for bug fixes (e.g., `bugfix/memory-leak`)
- `docs/` for documentation changes (e.g., `docs/api-reference`)
- `refactor/` for code refactoring (e.g., `refactor/response-engine`)

### Workflow Steps

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Add tests** for new functionality

4. **Run the test suite**:
   ```bash
   pytest
   flake8 .
   black . --check
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 88 characters (Black formatter default)
- **Imports**: Use absolute imports when possible
- **Type hints**: Use type hints for all public functions
- **Docstrings**: Follow Google-style docstrings

### Code Formatting

We use automated formatting tools:

- **Black**: Code formatting
  ```bash
  black .
  ```

- **isort**: Import sorting
  ```bash
  isort .
  ```

- **flake8**: Linting
  ```bash
  flake8 .
  ```

### Example Code Structure

```python
"""Module for handling deployment responses."""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DeploymentResponder:
    """Handles automated responses to deployment events.
    
    Args:
        config: Configuration dictionary for the responder.
        
    Attributes:
        config: The responder configuration.
        active: Whether the responder is currently active.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the deployment responder."""
        self.config = config
        self.active = True
        
    def handle_failure(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle deployment failure events.
        
        Args:
            event: The deployment failure event data.
            
        Returns:
            Response action dictionary if action taken, None otherwise.
            
        Raises:
            ValueError: If event data is invalid.
        """
        if not event.get('deployment_id'):
            raise ValueError("Event must contain deployment_id")
            
        logger.info(f"Handling deployment failure: {event['deployment_id']}")
        # Implementation here
        return {"action": "rollback", "deployment_id": event["deployment_id"]}
```

## Testing

### Test Structure

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

### Writing Tests

```python
import pytest
from responder.deployment import DeploymentResponder


class TestDeploymentResponder:
    """Test suite for DeploymentResponder class."""
    
    @pytest.fixture
    def responder(self):
        """Create a test responder instance."""
        config = {"rollback_enabled": True}
        return DeploymentResponder(config)
    
    def test_handle_failure_with_valid_event(self, responder):
        """Test handling a valid deployment failure event."""
        event = {"deployment_id": "dep-123", "status": "failed"}
        result = responder.handle_failure(event)
        
        assert result is not None
        assert result["action"] == "rollback"
        assert result["deployment_id"] == "dep-123"
    
    def test_handle_failure_with_invalid_event(self, responder):
        """Test handling an invalid deployment failure event."""
        event = {"status": "failed"}  # Missing deployment_id
        
        with pytest.raises(ValueError, match="Event must contain deployment_id"):
            responder.handle_failure(event)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_deployment.py

# Run with verbose output
pytest -v
```

## Documentation

### Documentation Standards

- **Docstrings**: All public functions and classes must have docstrings
- **Type hints**: Use type hints for better code documentation
- **Comments**: Use comments sparingly, prefer self-documenting code
- **README updates**: Update README.md when adding features

### API Documentation

For new API endpoints, include:
- Purpose and functionality
- Request/response examples
- Error codes and messages
- Authentication requirements

## Submitting Changes

### Pull Request Guidelines

1. **Clear title**: Use a descriptive title summarizing the change
2. **Detailed description**: Explain what changes were made and why
3. **Issue reference**: Link to related issues using `Fixes #123` or `Relates to #123`
4. **Screenshots**: Include screenshots for UI changes
5. **Breaking changes**: Clearly mark any breaking changes
6. **Testing**: Describe how the changes were tested

### Pull Request Template

When creating a PR, please use this template:

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review of code completed
- [ ] Comments added to hard-to-understand areas
- [ ] Documentation updated
- [ ] No new warnings introduced
```

## Review Process

### What to Expect

1. **Automated checks**: CI will run tests and linting
2. **Manual review**: Maintainers will review code and provide feedback
3. **Iteration**: You may need to make changes based on feedback
4. **Approval**: Once approved, your PR will be merged

### Review Criteria

- **Functionality**: Does the code work as intended?
- **Code quality**: Is the code readable and maintainable?
- **Tests**: Are there adequate tests for the changes?
- **Documentation**: Is documentation updated as needed?
- **Performance**: Are there any performance implications?

## Community

### Getting Help

- **GitHub Discussions**: For questions and general discussion
- **Issues**: For bug reports and feature requests
- **Discord/Slack**: [Link to be added] for real-time chat

### Recognition

Contributors are recognized in several ways:
- Listed in our [Contributors](CONTRIBUTORS.md) file
- Mentioned in release notes for significant contributions
- Given collaborator access for sustained contributions

## First-Time Contributors

Welcome! Here are some tips for first-time contributors:

1. **Start small**: Look for `good first issue` labels
2. **Ask questions**: Don't hesitate to ask for help
3. **Read the code**: Familiarize yourself with the codebase
4. **Follow examples**: Look at existing code for patterns
5. **Be patient**: The review process helps ensure quality

## License

By contributing to Autonomous DevOps Responder, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Autonomous DevOps Responder! Your help makes this project better for everyone. 🚀