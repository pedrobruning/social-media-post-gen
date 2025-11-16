## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ✅ Test improvements
- [ ] 🔧 Configuration changes

## Related Issues

<!-- Link to related issues using #issue_number -->
Closes #

## Changes Made

<!-- List the main changes made in this PR -->
-
-
-

## Testing

<!-- Describe the tests you ran and their results -->

**Test Coverage:**
- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Coverage maintained or improved

**Manual Testing:**
- [ ] Tested locally
- [ ] Tested with sample data
- [ ] Verified database migrations (if applicable)

## Checklist

**Before submitting, ensure you have:**

### Code Quality
- [ ] ✅ All tests pass locally (`uv run pytest tests/ -v`)
- [ ] 🎨 Code is formatted with Black (`uv run black src/ tests/`)
- [ ] 🔍 No linting errors (`uv run ruff check src/ tests/`)
- [ ] 📊 Code coverage maintained or improved
- [ ] 📝 Added/updated docstrings for new code
- [ ] 💬 Code is well-commented where necessary

### Database (if applicable)
- [ ] 🗄️ Database migrations created (`alembic revision --autogenerate`)
- [ ] ✅ Migrations tested (upgrade and downgrade)
- [ ] 📋 Repository tests added/updated

### Documentation
- [ ] 📚 README.md updated (if needed)
- [ ] 📄 CLAUDE.md updated with implementation details (if needed)
- [ ] 📋 TODO.md updated to reflect progress
- [ ] 💡 Added comments explaining complex logic

### Commits
- [ ] 📦 Commits are clear and descriptive
- [ ] 🔀 Branch is up-to-date with base branch
- [ ] 🧹 No unnecessary files included

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Additional Notes

<!-- Any additional information that reviewers should know -->

## CI/CD Status

The following checks must pass before merging:
- ✅ Tests (pytest with coverage)
- ✅ Linting (ruff)
- ✅ Format check (black)
- ✅ Migrations validation (alembic)
- ⚠️ Type checking (mypy - warnings only)
- ⚠️ Security scan (pip-audit - warnings only)

---

**Reminder**: Make sure all CI checks pass before requesting review!
