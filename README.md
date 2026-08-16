<div align="center">

# 📋 Korvexa Desktop Rich Clipboard (ClipVault)
### *Advanced, High-Performance Rich Clipboard Manager for Windows 10 & 11*

[![GitHub Stars](https://img.shields.io/github/stars/muhumair2025/Korvexa-Desktop-Rich-Clipboard?style=for-the-badge&logo=github&color=gold)](https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/muhumair2025/Korvexa-Desktop-Rich-Clipboard?style=for-the-badge&logo=github&color=blue)](https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard/network/members)
[![GitHub Release](https://img.shields.io/github/v/release/muhumair2025/Korvexa-Desktop-Rich-Clipboard?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard/releases)
[![Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows)](https://korvexa.app)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6 / Qt6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?style=for-the-badge&logo=qt)](https://www.qt.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20WAL%20%2B%20FTS5-003B57?style=for-the-badge&logo=sqlite)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Organization](https://img.shields.io/badge/Organization-Korvexa.app-0078d4?style=for-the-badge)](https://korvexa.app)

<br/>

<img src="images/popup%20clipboard%20model.png" width="500" alt="ClipVault Windows Rich Clipboard Popup" />

<p align="center">
  <b>Developed with ❤️ by <a href="https://korvexa.app">Muhammad Umair</a> for <a href="https://korvexa.app">Korvexa.app</a></b><br/>
  <i>Your ultimate local-first, zero-telemetry Windows clipboard companion with true rich-data support.</i>
</p>

[📥 Download Latest Installer](https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard/releases) • [✨ Key Features](#-key-features) • [⚡ Why ClipVault?](#-why-clipvault-comparison) • [📸 Screenshots](#-visual-tour--screenshots) • [⌨️ Shortcuts](#-keyboard-shortcuts) • [🛠️ Build from Source](#-building-from-source)

</div>

---

## 🌟 Overview

**ClipVault** by **Korvexa.app** is a production-grade, open-source Windows clipboard manager designed to transcend the limitations of the default `Win + V` clipboard. Built with **Python 3.12+**, **PySide6 (Qt6)**, **SQLite (WAL + FTS5 Full-Text Search)**, and **Native Win32 APIs**, it delivers lightning-fast capture, rich multi-format handling, smart non-overlapping popup placement, and complete offline privacy.

Whether you are copying multi-paragraph text, rich HTML, screenshots from Snipping Tool, files and directories from Windows Explorer, or website URLs, ClipVault preserves, indexes, and makes everything instantly accessible with a single click.

---

## ⚡ Why ClipVault? (Comparison)

| Feature | Windows `Win + V` | Generic Clipboard Tools | 📋 **ClipVault** |
| :--- | :---: | :---: | :---: |
| **Rich HTML & Plain Text Dual-Format** | ⚠️ Partial | ❌ No | ✅ **Full (Paste rich or plain)** |
| **Instant Single-Click Paste** | ❌ Multi-step | ⚠️ Inconsistent | ✅ **Yes (Instant `Ctrl+V`)** |
| **Smart Non-Overlapping Position** | ❌ Fixed | ❌ Overlaps input | ✅ **Dynamic (Above/Below input)** |
| **Explorer File Drop (`CF_HDROP`)** | ❌ No | ⚠️ Text path only | ✅ **Native File Drop structure** |
| **Topmost Modal Visibility** | ⚠️ Unstable | ❌ Buried behind dialogs | ✅ **Native `HWND_TOPMOST` guarantee** |
| **Screenshot Burst Debounce** | ❌ Duplicate events | ❌ Duplicate events | ✅ **120ms atomic coalescing** |
| **Full History Backup (Zip Export/Import)**| ❌ No | ⚠️ Complex DB copy | ✅ **1-Click `.zip` Migration** |
| **100% Offline / Zero Telemetry** | ❌ MS Account Sync | ⚠️ Varies | ✅ **100% Local-First** |
| **Sensitive Data Heuristic Filter** | ❌ No | ❌ No | ✅ **Auto-detect passwords & keys** |
| **SQLite FTS5 Full-Text Search** | ⚠️ Basic prefix | ⚠️ Slow substring | ✅ **Blazing FTS5 Indexing** |

---

## 🚀 Key Features

### 🖥️ Native Windows Integration
* **Event-Driven Win32 Clipboard Monitoring**: Uses `AddClipboardFormatListener` / `WM_CLIPBOARDUPDATE` combined with Qt's `dataChanged` signal to instantly capture clipboard modifications across all Windows applications.
* **Burst Coalescence & Debouncing**: Intelligent 120ms debounce pipeline eliminates duplicate records during rapid multi-format writes (e.g. `Win + Shift + S` Snipping Tool bursts).
* **Smart Non-Overlapping Placement**: Calculates screen geometry and automatically renders the popup **below or above** the active caret, ensuring your target text box is never covered.
* **Z-Order Topmost Guarantee**: Win32 `HWND_TOPMOST` positioning ensures ClipVault always displays in front of all modal windows, task managers, and system dialogs without stealing light-dismiss focus from Windows Search or Start Menu.
* **Auto-Start with Windows**: Starts silently minimized to the system tray on Windows boot (enabled by default).

### 🎨 Seamless Win + V Inspired UI
* **Single-Click Instant Paste**: Single-clicking any item immediately restores focus to your active application and executes a simulated `Ctrl + V` paste.
* **2-3 Line Natural Previews**: Generous card heights display formatted multi-line previews without ugly truncated one-liners.
* **Direct Image Previews**: Crisp, borderless aspect-scaled thumbnails without redundant dimension badges or grey inner boxes.
* **Light & Dark Themes**: Full Windows system theme detection with automatic real-time switching or manual preference override.
* **One-Click Clear All**: Header action button to quickly clear unpinned history with a confirmation safety prompt.

### 📦 Rich Multi-Format Support
| Format | Capabilities |
| :--- | :--- |
| **Plain Text** | Full unicode support, whitespace normalization, character and line counter badges. |
| **Rich HTML** | Dual-representation capture (`text/plain` + `text/html`). Supports rich paste and **Paste as Plain Text** (`Shift + Enter`). |
| **Images & Screenshots** | High-res PNG disk storage (`%LOCALAPPDATA%\ClipVault\media\images\`) with asynchronous Pillow thumbnail rendering. Supports "Open Image" and "Save Image As...". |
| **Files & Folders** | Windows Explorer `CF_HDROP` references. Restores native file drop structures on paste without duplicating disk files. |
| **Web URLs** | Automatic URL and domain recognition with instant "Open in Browser" and "Copy URL" actions. |

### 🔒 100% Local-First Privacy & Backup
* **Zero Telemetry & 100% Offline**: Your data never leaves your computer. No cloud sync, no tracking, no external API requests.
* **Heuristic Sensitive Data Protection**: Built-in pattern detection for credit cards, passwords, API tokens, and private keys.
* **Application Blacklist**: Ignore sensitive apps (e.g. `1password.exe`, `bitwarden.exe`, `keepass.exe`).
* **Backup & Migration**: Complete one-click Export and Import system (`.zip` backup archive) to preserve your database and media files across Windows installations.

---

## 📸 Visual Tour & Screenshots

<table align="center">
  <tr>
    <td align="center" width="50%">
      <b>📋 Main Clipboard Popup</b><br/>
      <img src="images/popup%20clipboard%20model.png" alt="Main Clipboard Popup" /><br/>
      <i>Flat cards with multi-line preview, search, categories, and instant single-click paste.</i>
    </td>
    <td align="center" width="50%">
      <b>⚡ Context Menu & Actions</b><br/>
      <img src="images/clipboard%20modle%20with%20item%20list%203%20dots%20menu%20open%20showing%20past%20open%20image%20save%20image%20as%20unpin%20pin%20etc.png" alt="Context Menu Actions" /><br/>
      <i>Rich format-specific actions: Paste plain text, open image, save as, pin, delete.</i>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>⚙️ General Preferences</b><br/>
      <img src="images/general%20settings.png" alt="General Settings" /><br/>
      <i>Windows auto-start, tray icon visibility, and audio feedback controls.</i>
    </td>
    <td align="center" width="50%">
      <b>📑 Supported Clipboard Formats</b><br/>
      <img src="images/clipboard%20settings.png" alt="Clipboard Settings" /><br/>
      <i>Toggle text, rich HTML, images, file drops, and URLs independently.</i>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>💾 History, Retention & Migration</b><br/>
      <img src="images/history%20settings.png" alt="History Settings" /><br/>
      <i>Retention rules, max history limit, and full Zip Backup Export / Import.</i>
    </td>
    <td align="center" width="50%">
      <b>🛡️ Privacy & Sensitive Detection</b><br/>
      <img src="images/privacy%20settings.png" alt="Privacy Settings" /><br/>
      <i>Credential auto-detection and custom process ignore blacklist.</i>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>⌨️ Global Shortcuts Configuration</b><br/>
      <img src="images/shortcuts%20settings.png" alt="Shortcuts Settings" /><br/>
      <i>Customize system-wide hotkey triggers (Default: Ctrl + Shift + V).</i>
    </td>
    <td align="center" width="50%">
      <b>🎨 Appearance & Theme Engine</b><br/>
      <img src="images/appearance%20settings.png" alt="Appearance Settings" /><br/>
      <i>Adaptive Windows System theme with manual Light and Dark mode overrides.</i>
    </td>
  </tr>
</table>

<div align="center">
  <b>🔧 Advanced Engine Settings</b><br/>
  <img src="images/advance%20settings.png" width="540" alt="Advance Settings" /><br/>
  <i>Fine-tune paste activation delays and clipboard restoration flags.</i>
</div>

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Ctrl + Shift + V`** | Open / Toggle ClipVault picker popup (Global system-wide hotkey) |
| **`Single Click`** / **`Enter`** | Paste selected item into previous window |
| **`Shift + Enter`** | Paste item as **Plain Text** |
| **`↑` / `↓` Arrow Keys** | Navigate up/down through history list |
| **`Ctrl + P`** | Toggle Pin status for the selected item |
| **`Delete`** | Delete selected item from history |
| **`Esc`** | Close clipboard picker window |

---

## 📥 Installation

### Method 1: Windows Setup Installer (Recommended)
1. Download the latest **`ClipVault_Setup_v1.0.0.exe`** from the [GitHub Releases](https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard/releases) page.
2. Run the installer wizard (includes desktop shortcut, Start menu entry, and auto-start options).
3. Press **`Ctrl + Shift + V`** anywhere in Windows to start copying and pasting!

---

## 🛠️ Building from Source

### Prerequisites
* **Windows 10 or 11 (64-bit)**
* **Python 3.12+**
* **Git**
* *(Optional)* **Inno Setup 6 or 7** (for compiling the installer)

### 1. Clone the Repository
```powershell
git clone https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard.git
cd Korvexa-Desktop-Rich-Clipboard
```

### 2. Set Up Virtual Environment & Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run the Application
```powershell
python main.py
```

### 4. Run Unit Tests
```powershell
python -m unittest discover tests -v
```

### 5. Build Standalone Executable
```powershell
python build.py
```
*The compiled binary will be generated at `dist\ClipVault.exe`.*

### 6. Compile Inno Setup Installer
```powershell
& "C:\Program Files\Inno Setup 7\ISCC.exe" "installer\setup.iss"
```
*The setup package will be generated at `dist_installer\ClipVault_Setup_v1.0.0.exe`.*

---

## 🏗️ Architecture & Project Structure

```text
Korvexa-Desktop-Rich-Clipboard/
├── main.py                          # Bootstrap, single-instance mutex & app loop
├── requirements.txt                 # Dependencies
├── ClipVault.spec                   # PyInstaller single-file bundle spec
├── build.py                         # Build automation script
├── .github/
│   ├── workflows/                   # GitHub Actions CI/CD release workflow
│   ├── ISSUE_TEMPLATE/              # Bug report & Feature request templates
│   └── pull_request_template.md     # Pull request template
├── CONTRIBUTING.md                  # Contribution guidelines
├── CODE_OF_CONDUCT.md               # Contributor Covenant code of conduct
├── SECURITY.md                      # Security reporting policy
├── installer/
│   ├── setup.iss                    # Modern Inno Setup script with Pascal code
│   ├── ABOUT.txt                    # App description page
│   ├── PRIVACY.txt                  # Privacy policy statement
│   └── LICENSE.txt                  # MIT License agreement
├── app/
│   ├── application.py               # ClipVaultApp main controller
│   ├── constants.py                 # Metadata, format types, global limits
│   └── theme.py                     # Light & Dark theme stylesheets & auto-detection
├── clipboard/
│   ├── monitor.py                   # Win32 AddClipboardFormatListener & debounce engine
│   ├── reader.py                    # Multi-format MIME reader & hierarchy extractor
│   ├── writer.py                    # Multi-format clipboard writer (Text/HTML/CF_HDROP)
│   ├── mime_parser.py               # Format detection & HTML-to-text converter
│   └── windows_clipboard.py         # Win32 ctypes (SendInput, SetWindowPos, CF_HDROP)
├── database/
│   ├── database.py                  # Thread-safe SQLite connection & WAL mode
│   ├── migrations.py                # Schema migrations & FTS5 full-text search
│   └── repositories.py              # Repositories for Clipboard items & Settings
├── models/
│   ├── clipboard_item.py            # Strongly-typed ClipboardItem model
│   ├── clipboard_file.py            # ClipboardFile metadata model
│   └── settings_model.py            # AppSettings data model
├── services/
│   ├── clipboard_service.py         # Capture, deduplication & processing pipeline
│   ├── history_service.py           # Retrieval, search & modification
│   ├── image_service.py             # Image storage & Pillow thumbnail generation
│   ├── paste_service.py             # Focus restoration & simulated SendInput paste
│   ├── backup_service.py            # Zip archive Export & Import migration engine
│   ├── privacy_service.py           # Regex heuristic sensitive data detector
│   └── startup_service.py           # Windows Registry auto-start manager
├── storage/
│   └── paths.py                     # %LOCALAPPDATA%\ClipVault storage resolution
├── ui/
│   ├── icons.py                     # SVG vector icon provider
│   └── widgets/
│       ├── item_card.py             # Flat list card widget
│       ├── search_bar.py            # Search input with keyboard navigation
│       └── category_bar.py          # Category pill filters
├── windows/
│   ├── clipboard_popup.py           # Main floating clipboard picker modal
│   ├── settings_window.py           # Multi-tab preferences window
│   ├── about_window.py              # About dialog with credits & links
│   └── text_editor_dialog.py        # Text editor modal
└── tests/                           # Comprehensive 28-test automated test suite
```

---

## 🤝 Contributing

Contributions, bug reports, and feature suggestions are warmly welcomed!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) or [`installer/LICENSE.txt`](installer/LICENSE.txt) for more details.

---

## 🏢 Organization & Credits

- **Organization**: [Korvexa.app](https://korvexa.app)
- **Developer**: **Muhammad Umair**
- **Website**: [https://korvexa.app](https://korvexa.app)
- **Support & Inquiries**: [support@korvexa.app](mailto:support@korvexa.app)
- **Repository**: [https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard](https://github.com/muhumair2025/Korvexa-Desktop-Rich-Clipboard)
