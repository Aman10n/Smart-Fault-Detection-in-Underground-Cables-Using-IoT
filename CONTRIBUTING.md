# Contributing

Thank you for helping improve the Smart Fault Detection project.

## Local setup

1. Fork and clone the repository.
2. Create a virtual environment with Python 3.10 or newer.
3. Install development dependencies:

   ```bash
   python -m pip install -r requirements-dev.txt
   ```

4. Create a focused branch from `main`.

## Quality checks

Run all checks before opening a pull request:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
node --check static/js/app.js
```

New backend behavior should include tests. Dashboard changes should remain usable on narrow screens and with keyboard navigation.

## Pull requests

- Explain the problem and the chosen solution.
- Keep unrelated changes out of the same pull request.
- Document new environment variables and API endpoints.
- Include screenshots for visible dashboard changes when practical.
- Never commit credentials, `.env` files, virtual environments, or generated caches.
