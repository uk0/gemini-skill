---
name: gemini-image
description: "Generate images using Google Gemini via browser automation. Two commands: (1) 'login' — open browser for Google account login, save session for reuse, (2) any image prompt — generate images in headless mode. Use when the user wants to: generate images with Gemini, create AI artwork, use Gemini image generation. Triggers on: 'gemini image', 'gemini generate', 'gemini 画图', 'gemini 生成图片', 'AI生成图像', or any request involving Gemini image creation."
---

# Gemini Image Generator

Two commands: `login` and image generation.

## First-time Setup

Install dependencies (only once):
```bash
cd <SKILL_DIR> && uv sync && uv run playwright install chromium
```

## Command: login

Opens a browser for the user to log into their Google account. Auto-detects login success and exits. Must be run before first image generation.

```bash
cd <SKILL_DIR>
uv run python scripts/gemini_image.py login
```

## Command: generate image

Generates images in headless mode (no browser window). Pass the prompt as argument.

```bash
cd <SKILL_DIR>
uv run python scripts/gemini_image.py "your prompt here"
```

Custom output directory:
```bash
cd <SKILL_DIR>
uv run python scripts/gemini_image.py -o /path/to/output "your prompt here"
```

Images are saved as PNG files in `output/` by default.

## Prompt Rules

- **NEVER** rewrite, optimize, or enhance the user's prompt. Pass it exactly as the user typed it.
- Only optimize the prompt if the user explicitly asks to (e.g. "优化一下提示词", "help me improve the prompt").
- The user's original wording is the prompt. Do not add style keywords, quality modifiers, or any extra text.

## How It Works

1. Launches headless Chromium with saved login session
2. Activates Gemini's "Create Image" tool
3. Sends the prompt, waits for `img.image.loaded` in DOM
4. Downloads via download button interception or canvas fallback
