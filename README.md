AI Terminal Assistant ✨

Natural-language to terminal commands with safe auto-execution.

---

## Features

### 🌟 Next-Gen Terminal Experience
- 🏠 Local AI Support (Ollama) & Cloud AI (Groq)
- 🔍 Context-aware error diagnosis
- 🪄 Natural language to command translation
- ⚡ Safe command execution workflows

## 🔧 Core Capabilities

### Error Diagnosis

```bash
# Error analysis example
$ rm -rf /important-folder
🔎 Analysis → 🛠️ Fix: `rm -rf ./important-folder`
```
![Error Analysis](screenshots/01_up.png)

### Natural Language to Commands

```bash
# Command generation (shortcut)
$ sa "find large files over 1GB"
# → find / -type f -size +1G -exec ls -lh {} \;
```
![Command generation](screenshots/02.png)

### ⚡ Interactive Workflows
- Confirm before executing generated commands
- Step-by-step complex operations
- Safety checks for destructive commands


### 🌐 Supported API Providers
- Groq
- OpenAI
- Anthropic 
- Fireworks.ai
- OpenRouter
- Deepseek

*Switch providers by editing `.env` (see Quick Setup below)*

---

## Installation

Requirements: Python 3.8+

```bash
git clone https://github.com/gulshandubbani2003/Terminal_assistant.git
cd Terminal_assistant
pip install -e .
```

### Configuration Notes
- Rename `.env.example` → `.env` and populate required values
- API performance varies by provider (Groq fastest, Anthropic most capable)
- Local models need 4GB+ RAM (llama3:8b) to 16GB+ (llama3:70b)
- Response quality depends on selected model capabilities


### Configure `.env`

Pick ONE mode at a time.

API mode (Gemini recommended):
```
MODE=api
ACTIVE_API_PROVIDER=gemini
API_MODEL=gemini-2.0-flash-exp
GEMINI_API_KEY=YOUR_API_KEY
```

Local mode (free/offline via Ollama):
```
MODE=local
OLLAMA_HOST=http://localhost:11434
LOCAL_MODEL=llama3.2:3b
```

---



## Shortcut command `sa` (recommended)

PowerShell (Windows):
```powershell
notepad $PROFILE
# Paste and save:
function sa {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$args)
  shellsage ask --execute ($args -join ' ')
}
. $PROFILE
```

Optional CMD + PowerShell wrapper (create `%USERPROFILE%\\bin\\sa.cmd` and add that folder to PATH):
```cmd
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "shellsage ask --execute ($args -join ' ')" -- %*
```

Examples:
```bash
sa "list files in current directory"
sa "create a new txt file named hi.txt and write hello in it"
sa "ssh -i C:\\Keys\\aws.pem ubuntu@1.2.3.4"
```

---

## Development Status 🚧

This project is currently in **alpha development**.  

**Known Limitations**:
- Limited Windows support
- Compatibility issues with zsh, fish
- Occasional false positives in error detection
- API mode requires provider-specific key

**Roadmap**:
- [x] Local LLM support
- [x] Hybrid cloud(api)/local mode switching
- [x] Model configuration wizard
- [ ] Better Context Aware
- [ ] Windows PowerShell integration
- [ ] Tmux Integration
- [ ] CI/CD error pattern database

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feat/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feat/amazing-feature`)
5. Open Pull Request

---


> **Note**: This project is not affiliated with any API or model providers.  
> Local models require adequate system resources.
> Internet required for initial setup and API mode.  
> Use at your own risk with critical operations.
> Always verify commands before execution
