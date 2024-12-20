# Bouncer

Bouncer screens iMessages for you, and lets you know when you get important ones.

## Demo
![Uploading bouncer.gif…]()

## Setup

```
# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# install ollama
brew install ollama

# clone the repo
git clone https://github.com/meltylabs/bouncer.git

# run the bouncer
uv run bouncer.py
```

## Customize your bouncer

You can customize your bouncer by updating the `SHIBBOLETH` and `GATEKEEPER_PROMPT` variables in `bouncer.py`.

## Requirements

- Python >= 3.12 (but I think this will work on most versions)
- [Ollama](https://ollama.ai/)
- [uv](https://docs.astral.sh/uv/)
