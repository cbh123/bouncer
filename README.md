# Bouncer

I often get distracted checking my new messages on my Mac. So I created my very own Bouncer to notify me when I get anything important. Bouncer is free, completely private, and open source.

Here's how it works:
- Every 2 seconds, Bouncer checks the local iMessage database
- When a new one comes in, it asks a locally running llama3.2 if the message is important OR if the message contains a special Shibboleth word.
  - If important, Bouncer sends me a notification with a link to open the message window and respond.
  - If not, Bouncer screens it out and I continue my day distraction free :)

## Demo
![bouncer](https://github.com/user-attachments/assets/b1f240d5-1a1d-412f-9fac-b88efb962b10)


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
