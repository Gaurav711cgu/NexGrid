## Change Type
- [ ] 🚀 Feature
- [ ] 🐛 Bug Fix
- [ ] ⚙️ Refactor
- [ ] 📚 Documentation
- [ ] 🛡️ Security / Hotfix

## Summary
<!-- Concise description of changes. Reference issue numbers where applicable. -->

## Key Architecture & Design Decisions
<!-- Why was this approach chosen over alternatives? (Reference ADRs if applicable) -->

## Testing Checklist
- [ ] Unit tests added / updated
- [ ] Integration tests pass locally (`pytest backend/tests/ -v`)
- [ ] Coverage threshold met (`pytest --cov=backend/app --cov-fail-under=85`)
- [ ] Lint check passed (`ruff check backend/app`)
- [ ] Type check passed (`mypy backend/app`)

## Security & System Design Impact
- [ ] No breaking change to API contracts or auth behavior
- [ ] Auth / Security logic modified — verified with security owner
- [ ] Verified non-root Docker build (`docker build -t app ./backend`)
