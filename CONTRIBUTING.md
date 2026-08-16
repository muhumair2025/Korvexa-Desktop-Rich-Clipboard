# Contributing to Korvexa Desktop Rich Clipboard (ClipVault)

First off, thank you for considering contributing to **ClipVault**! It's people like you that make open-source software so vibrant.

---

## 📋 Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## 🛠️ How Can I Contribute?

### 1. Reporting Bugs
- Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
- Ensure the bug was not already reported by searching on GitHub under [Issues](https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard/issues).
- Provide clear steps to reproduce, expected vs. actual behavior, and your Windows version.

### 2. Suggesting Enhancements
- Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).
- Explain why this enhancement would be useful to most users.

### 3. Pull Requests
1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Set up the development environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Ensure all automated unit tests pass:
   ```powershell
   python -m unittest discover tests -v
   ```
4. Commit your changes following conventional commit syntax (`feat: ...`, `fix: ...`, `docs: ...`):
   ```bash
   git commit -m "feat: add customizable card corner radius"
   ```
5. Push to your branch and submit a Pull Request to `main`.

---

## 🏗️ Development Guidelines

- **Clean Architecture**: Maintain separation between UI widgets (`ui/widgets/`), backend services (`services/`), database repositories (`database/`), and Win32 ctypes hooks (`clipboard/`).
- **No Heavy Dependencies**: Avoid adding bulky third-party dependencies unless strictly necessary.
- **Offline First**: Never introduce external telemetry, analytics, or cloud sync without explicit opt-in.

---

## 📜 Questions & Support
- Join discussions or open an issue on GitHub.
- Reach out to the core team at [support@korvexa.app](mailto:support@korvexa.app).
