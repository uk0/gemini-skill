# Gemini Web Skill

Generate images using Google Gemini through browser automation with Playwright.

## Features

- One-command image generation via Gemini AI
- Persistent login session (login once, reuse forever)
- Headless mode by default (no browser window)
- Download button interception + canvas fallback
- Standalone skill package for easy distribution

## Quick Start

```bash
# Install dependencies
uv sync
uv run playwright install chromium

# Login (first time only - opens browser)
uv run python src/gemini_image.py login

# Generate images
uv run python src/gemini_image.py "a cute cat on the moon"
```

## Skill Package

The `skill/gemini-image/` directory is a self-contained package you can copy anywhere:

```
skill/gemini-image/
├── SKILL.md
├── pyproject.toml
├── scripts/
│   └── gemini_image.py
├── userdata/          (auto-created, gitignored)
└── output/            (auto-created, gitignored)
```

### Usage

```bash
cd skill/gemini-image
uv sync && uv run playwright install chromium

# Login
uv run python scripts/gemini_image.py login

# Generate (headless by default)
uv run python scripts/gemini_image.py "画一只小狗"

# Show browser window
uv run python scripts/gemini_image.py --no-headless "draw a dog"

# Custom output dir
uv run python scripts/gemini_image.py -o ./my-images "sunset over mountains"
```

## Project Structure

```
├── src/
│   ├── gemini_image.py    # Main generator (dev version)
│   └── recorder.py        # Request recorder for API analysis
├── skill/gemini-image/    # Standalone skill package
├── recordings/            # Recorded sessions (gitignored)
├── userdata/              # Browser login data (gitignored)
└── output/                # Generated images (gitignored)
```

## How It Works

1. Launches Chromium with persistent user data (saved Google login)
2. Navigates to Gemini and activates the "Create Image" tool
3. Types the prompt and sends it
4. Monitors DOM for `img.image.loaded` elements
5. Downloads images via download button or canvas extraction

## License

MIT
