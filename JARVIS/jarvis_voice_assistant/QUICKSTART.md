# JARVIS Quick Start Guide

## 5-Minute Setup

### 1. Clone Project

```bash
git clone <repo> jarvis_voice_assistant
cd jarvis_voice_assistant
```

### 2. Run Setup Script

```bash
python setup.py
```

This will:
- ✓ Create Python virtual environment
- ✓ Install all dependencies
- ✓ Download speech recognition models
- ✓ Generate encryption key

### 3. Set Encryption Key

From setup output, copy your encryption key and set it:

```bash
# macOS/Linux
export JARVIS_ENCRYPTION_KEY="your_key_here"

# Windows PowerShell
$env:JARVIS_ENCRYPTION_KEY="your_key_here"
```

### 4. Enroll Your Voice

```bash
python src/main.py --enroll
```

- Speak 7 different sentences
- Each ~4 seconds long
- Speak naturally and clearly
- Minimize background noise

**Example sentences:**
1. "Hello Jarvis, this is my voice"
2. "I am ready to give you commands"
3. "Recognize me for future authentication"
4. "Security and privacy matter to me"
5. "This is my unique voice fingerprint"
6. "Please accept my voice for verification"
7. "Thank you for protecting my privacy"

### 5. Test Verification

```bash
python src/main.py --verify
```

- Speak any sentence (same voice as enrollment)
- If verified: "✓ VERIFICATION PASSED"
- Try a command like "What time is it?"

### 6. Run Interactive Mode

```bash
python src/main.py --interactive
```

- Keeps listening for voice input
- Press ENTER before speaking
- Press CTRL+C to exit
- Your voice controls everything

---

## Common Commands

After verification, try these:

```
"What time is it?"
"Today's date"
"Open browser"
"Open notepad"
"Play music"
"System status"
"List commands"
```

---

## Troubleshooting Quick Fixes

### Issue: No microphone found

```bash
python src/main.py --list-devices
```

Find your microphone number, edit `config/settings.yaml`:

```yaml
audio:
  device_index: 2  # Change this number
```

### Issue: Verification keeps failing

1. Try adjusting threshold in `config/settings.yaml`:

```yaml
verification:
  similarity_threshold: 0.65  # Lower = more lenient
```

2. Re-enroll if you sound different:

```bash
rm data/voiceprint.encrypted
python src/main.py --enroll
```

### Issue: "STT not recognizing commands"

Speak slower and more clearly. Vosk works best with distinct pronunciation.

### Issue: "Encryption key error"

Make sure environment variable is set:

```bash
# Check if key is set
echo $JARVIS_ENCRYPTION_KEY

# If empty, set it again
export JARVIS_ENCRYPTION_KEY="your_key"
```

---

## What's Happening Behind The Scenes

```
1. You speak
    ↓
2. Audio captured (16kHz mono)
    ↓
3. Speaker embedding extracted (512-dim vector)
    ↓
4. Compared with your stored voiceprint
    ↓
5. If 70%+ match → VERIFIED
    ↓
6. Your speech transcribed to text
    ↓
7. Command intent parsed
    ↓
8. Command executed safely
    ↓
9. Audit logged (no PII)
```

---

## Security Checklist

✓ Your voice is NEVER stored (only encrypted embedding)
✓ Audio is NEVER logged
✓ All data stays on your computer (100% offline)
✓ Encryption key is required to access voiceprint
✓ Only whitelisted commands can execute
✓ All attempts are logged for audit trail

---

## Next Steps

1. **Customize commands** → Edit `config/commands.yaml`
2. **Adjust security** → Edit `config/thresholds.yaml`
3. **Review logs** → `cat logs/access.log`
4. **Read full docs** → [README.md](README.md)
5. **Security details** → [SECURITY.md](SECURITY.md)

---

## Help & Support

**Installation Issues:**
- See [README.md](README.md) → Installation & Setup

**Security Questions:**
- See [SECURITY.md](SECURITY.md) → Threat Analysis

**Advanced Configuration:**
- See [README.md](README.md) → Configuration & Tuning

**Running Tests:**
```bash
python -m pytest tests/ -v
```

---

**You're ready! Run:** `python src/main.py --verify`
