# Security Policy

## Supported version

Security fixes are applied to the latest revision of the `main` branch.

## Reporting a vulnerability

Please use GitHub's **Report a vulnerability** option under the repository's Security tab when private vulnerability reporting is available. Do not include exploit details, credentials, or personal data in a public issue.

Include:

- the affected endpoint, event, or file;
- steps to reproduce the problem;
- the likely impact;
- any suggested remediation.

## Deployment guidance

- Set a long, random `SECRET_KEY` in deployed environments.
- Limit `CORS_ALLOWED_ORIGINS` to trusted dashboard origins.
- Keep debug mode disabled outside local development.
- Bind to `127.0.0.1` unless a reverse proxy or container requires another interface.
- Terminate TLS at a trusted reverse proxy for network deployments.
- Treat the fault controls as administrative functions and add authentication before exposing them beyond a trusted demonstration environment.

This repository simulates IoT telemetry and is not intended to control live electrical infrastructure.
