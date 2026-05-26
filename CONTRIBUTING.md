# CONTRIBUTING.md

## Contributing Guidelines

Thank you for your interest in contributing to the Financial Risk Lakehouse project!

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone <your-fork-url>`
3. **Create** a feature branch: `git checkout -b feature/your-feature-name`
4. **Install** dependencies: `pip install -r requirements.txt`
5. **Set up** environment: `source scripts/setup_env.sh`

## Development Workflow

### Code Style

We follow PEP 8 and use automated formatters:

```bash
# Format code
black . && isort .

# Lint code
flake8 .

# Type check
mypy .
```

### Testing

All code changes must include tests:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test
pytest tests/unit/test_logger.py -v
```

### Commit Messages

Follow conventional commits format:

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(pipelines): add new data quality check

Add comprehensive quality validation for Bronze layer
including null checks and duplicate detection.

Fixes #123
```

## Pull Request Process

1. Update documentation
2. Add/update tests
3. Run full test suite locally
4. Create PR with clear description
5. Ensure CI/CD passes
6. Wait for code review
7. Address feedback
8. Merge after approval

## Coding Standards

### Python
- Python 3.10+
- Type hints for all functions
- Docstrings for classes and functions
- Max line length: 100 characters

### SQL (dbt)
- Descriptive table/column names
- Schema.yml documentation
- Singular tests for complex logic
- Generic tests for data quality

### Configuration
- Use environment variables for secrets
- Document all configuration options
- Version control configs (not values)

## Project Structure

When adding new features:

```
feature/
├── implementation/
│   ├── pipelines/...
│   ├── tests/...
│   └── docs/...
└── PR description
```

## Areas for Contribution

### High Priority
- [ ] Data quality enhancements
- [ ] Performance optimizations
- [ ] Documentation improvements
- [ ] Test coverage expansion
- [ ] Security hardening

### Medium Priority
- [ ] New data sources
- [ ] Additional transformations
- [ ] API endpoints
- [ ] Visualization improvements

### Low Priority
- [ ] Code cleanup
- [ ] Style improvements
- [ ] Dependency updates

## Reporting Issues

Create an issue with:
1. Clear title
2. Detailed description
3. Steps to reproduce
4. Expected vs actual behavior
5. Environment details

## Getting Help

- **Documentation**: Check `/docs` folder
- **Issues**: Search existing issues
- **Discussions**: Start a discussion
- **Slack**: #data-platform channel
- **Email**: data-platform@company.com

## Code of Conduct

- Be respectful and inclusive
- Assume good intentions
- Focus on constructive feedback
- Help others succeed

## License

By contributing, you agree your code will be licensed under the MIT License.

---

Questions? Don't hesitate to ask!
