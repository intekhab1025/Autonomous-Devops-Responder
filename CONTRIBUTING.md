# Contributing to Autonomous DevOps Responder

Thank you for your interest in contributing to the Autonomous DevOps Responder! We welcome contributions from the community.

## 🚀 How to Contribute

### 1. Fork and Clone
```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/Autonomous-Devops-Responder.git
cd Autonomous-Devops-Responder
```

### 2. Create a Branch
```bash
# Create a feature branch from main
git checkout -b feature/your-feature-name
# or for bug fixes
git checkout -b fix/bug-description
```

### 3. Make Changes
- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 4. Test Your Changes
```bash
# Run any existing tests
# Test your changes thoroughly
# Ensure no regressions
```

### 5. Submit a Pull Request
- Push your branch to your fork
- Create a Pull Request against the `main` branch
- Fill out the PR template completely
- Link any related issues

## 📋 Contribution Guidelines

### Code Standards
- Follow Python PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Include type hints where appropriate

### Commit Messages
Use conventional commit format:
```
type(scope): description

feat(ui): add new dashboard widget
fix(k8s): resolve deployment scaling issue
docs(readme): update installation instructions
```

### Areas for Contribution
- 🐛 **Bug Fixes**: Help us identify and fix issues
- ✨ **New Features**: Enhance the platform capabilities
- 📚 **Documentation**: Improve guides and documentation
- 🧪 **Testing**: Add test coverage
- 🎨 **UI/UX**: Improve the Streamlit dashboard
- 🔧 **Infrastructure**: Enhance Terraform modules
- 🚀 **Performance**: Optimize AI agent performance

### Review Process
1. All contributions require review by project maintainers
2. PRs must pass all checks and tests
3. Maintainer will provide feedback and merge approved changes
4. Large changes should be discussed in an issue first

## 🛠️ Development Setup

### Prerequisites
- Python 3.9+
- Docker
- kubectl
- Terraform >= 1.5.0
- AWS CLI

### Local Development
```bash
# Install dependencies
pip install -r app/requirements.txt

# Set up pre-commit hooks (optional)
pre-commit install

# Run the application locally
cd app
streamlit run src/ui/dashboard.py
```

## 📞 Getting Help

- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Issues**: Report bugs via GitHub Issues
- 📧 **Contact**: Reach out to maintainers for complex questions

## 🏆 Recognition

Contributors will be:
- Listed in the project's contributor section
- Credited in release notes for significant contributions
- Invited to join the project as collaborators for consistent contributions

## 📜 Code of Conduct

By participating in this project, you agree to:
- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment
- Follow project guidelines and standards

Thank you for helping make Autonomous DevOps Responder better! 🚀
