"""
JARVIS Installation & Setup Script
Automates environment setup and dependency installation.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def run_command(cmd, description=""):
    """Run shell command with error handling."""
    if description:
        print(f"  → {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error: {e.stderr}")
        return False

def setup_environment():
    """Setup Python virtual environment."""
    print_header("Setting Up Python Virtual Environment")
    
    system = platform.system()
    venv_path = Path("venv")
    
    # Create venv
    if not venv_path.exists():
        print("  Creating virtual environment...")
        python_exe = "python3" if system != "Windows" else "python"
        run_command(f"{python_exe} -m venv venv", "Virtual environment")
    
    # Determine activation command
    if system == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"
    
    print(f"\n  Virtual environment ready!")
    print(f"  Activate with: {activate_cmd}")
    return activate_cmd

def install_dependencies():
    """Install Python packages."""
    print_header("Installing Python Dependencies")
    
    system = platform.system()
    pip_cmd = "pip" if system == "Windows" else "pip3"
    
    # Upgrade pip
    print("  Upgrading pip...")
    run_command(f"{pip_cmd} install --upgrade pip", "")
    
    # Install PyTorch CPU
    print("\n  Installing PyTorch (CPU)...")
    run_command(
        f"{pip_cmd} install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
        "PyTorch"
    )
    
    # Install other dependencies
    print("\n  Installing other packages...")
    run_command(f"{pip_cmd} install -r requirements.txt", "Requirements")

def download_models():
    """Download required models."""
    print_header("Downloading AI Models")
    
    models_dir = Path("models/speech_recognition")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    vosk_dir = models_dir / "vosk-model-small-en-us-0.15"
    
    if vosk_dir.exists():
        print(f"  ✓ Vosk model already exists")
        return
    
    print("  Downloading Vosk speech recognition model (~40MB)...")
    print("  This may take 1-2 minutes...")
    
    url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    zip_path = models_dir / "vosk.zip"
    
    # Download
    try:
        import urllib.request
        urllib.request.urlretrieve(url, zip_path)
        print("  ✓ Download complete")
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        print(f"  Manual download: {url}")
        return
    
    # Extract
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        zip_path.unlink()
        print("  ✓ Model extracted")
    except Exception as e:
        print(f"  ✗ Extraction failed: {e}")

def create_encryption_key():
    """Generate and display encryption key."""
    print_header("Generating Encryption Key")
    
    try:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        
        print("\n  Your encryption key (SAVE THIS SECURELY!):\n")
        print(f"  {key}\n")
        print("  Set environment variable:")
        print(f"\n  macOS/Linux:")
        print(f"    export JARVIS_ENCRYPTION_KEY=\"{key}\"")
        print(f"\n  Windows (PowerShell):")
        print(f"    $env:JARVIS_ENCRYPTION_KEY=\"{key}\"")
        print(f"\n  Windows (CMD):")
        print(f"    set JARVIS_ENCRYPTION_KEY={key}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")

def verify_installation():
    """Verify all components are installed."""
    print_header("Verifying Installation")
    
    try:
        import torch
        print(f"  ✓ PyTorch {torch.__version__}")
    except ImportError:
        print("  ✗ PyTorch not installed")
        return False
    
    try:
        import speechbrain
        print(f"  ✓ SpeechBrain installed")
    except ImportError:
        print("  ✗ SpeechBrain not installed")
        return False
    
    try:
        import sounddevice
        print(f"  ✓ SoundDevice installed")
    except ImportError:
        print("  ✗ SoundDevice not installed")
        return False
    
    try:
        import vosk
        print(f"  ✓ Vosk installed")
    except ImportError:
        print("  ✗ Vosk not installed")
        return False
    
    try:
        from cryptography.fernet import Fernet
        print(f"  ✓ Cryptography installed")
    except ImportError:
        print("  ✗ Cryptography not installed")
        return False
    
    # Check models
    if Path("models/speech_recognition/vosk-model-small-en-us-0.15").exists():
        print(f"  ✓ Vosk models downloaded")
    else:
        print(f"  ✗ Vosk models not found")
        return False
    
    return True

def main():
    """Run complete setup."""
    print("\n")
    print("  ╔════════════════════════════════════════╗")
    print("  ║  JARVIS Voice Assistant - Setup Script ║")
    print("  ║  Offline Voice Authentication System   ║")
    print("  ╚════════════════════════════════════════╝")
    
    # Setup steps
    try:
        setup_environment()
        install_dependencies()
        download_models()
        create_encryption_key()
        
        print_header("Setup Complete!")
        
        if verify_installation():
            print("\n  ✓ All components installed successfully!\n")
            print("  Next steps:")
            print("    1. Set your encryption key (see above)")
            print("    2. Run enrollment: python src/main.py --enroll")
            print("    3. Test verification: python src/main.py --verify")
            print("\n")
        else:
            print("\n  ⚠ Some components missing. Check error messages above.")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n  ✗ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
