# QR Generator SC

A modern, feature-rich QR code generator with beautiful dark/light theme support, real-time preview, custom styling options, and persistent storage of generation history.

## Overview

QR Generator SC is a professional-grade QR code generation application built with [Flet](https://flet.dev/) and Python. It provides an intuitive interface for creating QR codes with full customization capabilities including custom colors, sizes, margins, and supports multiple QR code types (URL, Email, Text). The application maintains a generation history with persistent settings and offers seamless switching between dark and light themes.

## Key Features

- **Multiple QR Types**: Generate QR codes for URLs, email addresses, and plain text content
- **Custom Styling**: Full color customization (foreground and background), adjustable size (256x256 to 1024x1024 px), and margin control
- **Real-time Preview**: Instant QR code preview as you adjust settings and content
- **Generation History**: Persistent storage of previously generated QR codes with quick access and reload capability
- **Dark/Light Themes**: Toggle between professional dark and light themes without losing your work
- **One-Click Export**: Download generated QR codes as PNG files
- **PDF Export**: Export single or multiple QR codes as PDF documents
- **Batch Export**: Generate and export multiple QR codes at once from history
- **Persistent Settings**: Automatically saves your color preferences, size, and margin settings across sessions
- **Modern UI**: Clean, flat design system with accessible color tokens and responsive layout

## Quick Start

### Installation

### Option A: Download Pre-built Executable (Windows)

1. Go to [Releases](https://github.com/sebastianmct/qr-generator-sc/releases)
2. Download `QRGeneratorSC.exe` 
3. Run it directly (no Python installation needed)

### Option B: Run from Source (Requires Python 3.8+)

1. Clone the repository:
   ```bash
   git clone https://github.com/sebastianmct/qr-generator-sc
   cd qr_generator_sc
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run:
   ```bash
   python main.py
   ```

The application will launch with the default light theme. Use the theme toggle button to switch to dark mode.

## Usage

### Generating a QR Code

1. **Select QR Type**: Choose from URL, Text, Email, WiFi, WhatsApp, SMS, Phone, GPS, or vCard using the dropdown menu
2. **Enter Content**: Fill in the dynamic fields for the selected type (e.g. SSID/password for WiFi, phone number for WhatsApp)
3. **Customize Appearance** (optional):
   - Click the color swatches or enter hex values to change foreground/background colors
   - Select a size from the dropdown (256, 512, 1024 pixels)
   - Adjust the margin value (border around the QR code)
4. **Preview**: The QR code updates in real-time as you modify settings
5. **Download**: Click the "Download QR Code" button to save as PNG
6. **Export SVG**: Under **Export As → SVG**, click **Export** to save a vector `.svg` file
7. **Export PDF**: Under **Export As → PDF**, click **Export** to save as a PDF document

### Batch Export

Generate and export multiple QR codes at once from your history:

1. Click the **"Batch Export"** button in the history panel
2. Select the QR codes you want to include in the export
3. Choose the export format (PNG or PDF)
4. Click **"Export Selected"** to generate a zip file containing all selected QR codes

### Managing History

The left sidebar displays all previously generated QR codes. Click any entry to:
- Pre-fill the form with that QR code's settings
- View the original content and customization options
- Make modifications and regenerate

### Language / Idioma

Use the **flag button** (🇺🇸 / 🇪🇸) in the top bar to toggle between **English** and **Español**. The choice is saved automatically and applied instantly without losing form data or the current QR preview.

### Theme Management

Use the theme toggle (icon in the header) to switch between dark and light themes. All your current work, color customization, and form state are preserved during the theme switch.

## Architecture

The application follows a clean, layered architecture:

```
qr_generator_sc/
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── qr_generator_sc.spec     # PyInstaller configuration
├── README.md                # Documentation
├── assets/                  # Icons and images
│
├── ui/                      # User interface components
│   ├── app_shell.py         # Main application container and theme management
│   ├── generator_view.py    # QR generation form and preview
│   ├── history_panel.py     # Generation history sidebar
│   ├── project_panel.py     # Project management
│   ├── batch_export_dialog.py # Batch export dialog
│   └── components.py        # Reusable UI components
│
├── services/                # Business logic layer
│   ├── qr_service.py        # QR code image generation and export
│   ├── svg_export_service.py # Vector SVG export
│   ├── pdf_export_service.py # PDF export service
│   ├── multipage_pdf_export_service.py # Multi-page PDF export service
│   ├── qr_content_service.py # Field validation and payload building
│   └── logo_service.py      # Logo processing
│
├── qr_types/                # QR payload builders
│   ├── base.py              # Builder base class and field definitions
│   ├── simple_builders.py   # URL, Text, Email
│   ├── wifi_builder.py
│   ├── whatsapp_builder.py
│   ├── sms_builder.py
│   ├── phone_builder.py
│   ├── gps_builder.py
│   └── vcard_builder.py
│
├── validators/              # Shared field validators
│   └── common.py
│
├── i18n/                    # Internationalization
│   ├── translation_manager.py
│   ├── translations_en.py
│   └── translations_es.py
│
├── models/                  # Data models
│   └── qr_entry.py          # QR code entry data structure
│   └── project.py           # Project model
│
├── storage/                 # Data persistence layer
│   ├── history_storage.py   # History JSON persistence
│   ├── project_storage.py   # Projects JSON + folders
│   └── settings_storage.py  # Settings and preferences persistence
│
└── themes/                  # Design system
    ├── theme_manager.py     # Theme state and color resolution
    └── tokens.py            # Design tokens and color definitions
```

### Core Components

**qr_service.py**: Handles QR code generation using the `qrcode` library with PIL backend. Supports preview generation at 240px (for display) and configurable export sizes (256, 512, 1024 px) with custom margins and colors.

**pdf_export_service.py**: Provides PDF export functionality for single QR codes, generating properly formatted PDF documents with embedded QR code images.

**multipage_pdf_export_service.py**: Handles multi-page PDF export for batch operations, creating PDF documents with multiple QR codes arranged across pages.

**batch_export_dialog.py**: UI component for batch export functionality, allowing users to select multiple QR codes from history and export them in various formats (PNG or PDF)

**theme_manager.py**: Central theme management system providing color token resolution. Supports light/dark mode toggle while preserving application state during transitions.

**storage/**: Dual persistence layer:
- `history_storage.py`: Maintains a list of generated QR codes with their settings
- `settings_storage.py`: Persists user preferences including theme selection, default colors, size, and margin

## Requirements

- Python 3.10+
- Flet 0.85.2
- qrcode[pil]
- Pillow

See `requirements.txt` for the complete dependency list and installation instructions.

## Configuration

Settings are automatically saved to `~/.qr_generator_sc/settings.json`:

```json
{
  "theme": "light",
  "qr_foreground_color": "#000000",
  "qr_background_color": "#FFFFFF",
  "qr_size": 512,
  "qr_margin": 4,
  "last_qr_type": "URL"
}
```

Generated QR codes history is stored in `~/.qr_generator_sc/history.json`.

> **Note**: Settings are managed through the UI. Manual editing of configuration files is not recommended as the application will overwrite them on next launch.

## Troubleshooting

> **QR Code not generating?** Ensure the content field is not empty and matches the selected QR type. For email, use a complete email address; for URL, include the protocol (http:// or https://).

> **Theme toggle not working?** Restart the application. Your settings are automatically saved, so your preferences will be restored on next launch.

> **Previous QR codes not showing in history?** Check that `~/.qr_generator_sc/history.json` exists and is readable. You may need to generate a new QR code to initialize the history file.

## Building a Distributable

### macOS / Linux

```bash
pyinstaller qr_generator_sc.spec
# Output: dist/QRGeneratorSC
```

### Windows

```bash
pyinstaller qr_generator_sc.spec
# Output: dist/QRGeneratorSC.exe
```

---

## Design System

This project follows the **Flat Design System** (typeui.sh) strictly:

| Token | Value |
|---|---|
| Primary | `#F2673C` |
| Secondary | `#8B5CF6` |
| Success | `#16A34A` |
| Warning | `#D97706` |
| Danger | `#DC2626` |
| Font | Inter / JetBrains Mono |
| Spacing | 4 / 8 / 12 / 16 / 24 / 32 |

No gradients, no 3D shadows, no decorative motion without purpose.

---

## Architecture Principles

- **OOP + SOLID** — each class has a single responsibility
- **Separation of Concerns** — UI / Services / Storage / Themes / Models are fully isolated
- **Dependency injection** — `ThemeManager` and `HistoryStorage` are injected, not imported globally
- **Flat component factory** — `FlatComponents` reads live theme tokens; re-theming is instant

---

## Built With

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flet](https://img.shields.io/badge/Flet-0D6EFD?style=for-the-badge)
![QRCode](https://img.shields.io/badge/QRCode-000000?style=for-the-badge)
![Pillow](https://img.shields.io/badge/Pillow-9CF?style=for-the-badge&logo=pillow&logoColor=white)
![ReportLab](https://img.shields.io/badge/ReportLab-red?style=for-the-badge)
![PyInstaller](https://img.shields.io/badge/PyInstaller-1D4ED8?style=for-the-badge&logo=pyinstaller&logoColor=white)
![SVG](https://img.shields.io/badge/SVG-FFB13B?style=for-the-badge&logo=svg&logoColor=black)