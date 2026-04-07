"""
Ollama Setup Helper for Windows
Provides utilities to verify and manage Ollama installation
"""

import subprocess
import asyncio
import httpx
from pathlib import Path


class OllamaSetup:
    """Helper class for Ollama setup and verification"""
    
    OLLAMA_API_URL = "http://localhost:11434"
    OLLAMA_INSTALL_PATH = Path.home() / "AppData" / "Local" / "Programs" / "Ollama"
    
    @staticmethod
    async def check_api_connection() -> bool:
        """Check if Ollama API is responding"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{OllamaSetup.OLLAMA_API_URL}/api/tags")
                return response.status_code == 200
        except Exception as e:
            print(f"✗ API connection failed: {e}")
            return False
    
    @staticmethod
    def check_installation() -> bool:
        """Check if Ollama is installed"""
        ollama_exe = OllamaSetup.OLLAMA_INSTALL_PATH / "ollama.exe"
        return ollama_exe.exists()
    
    @staticmethod
    def get_version() -> str:
        """Get Ollama version"""
        try:
            ollama_exe = OllamaSetup.OLLAMA_INSTALL_PATH / "ollama.exe"
            result = subprocess.run(
                [str(ollama_exe), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {e}"
    
    @staticmethod
    async def get_models() -> list:
        """Get list of downloaded models"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{OllamaSetup.OLLAMA_API_URL}/api/tags")
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return models
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []


async def verify_ollama_setup():
    """Verify complete Ollama setup"""
    print("=" * 70)
    print("OLLAMA SETUP VERIFICATION")
    print("=" * 70)
    
    setup = OllamaSetup()
    
    # Check 1: Installation
    print("\n[1] Installation Check...")
    if setup.check_installation():
        print(f"  ✓ Ollama installed at: {setup.OLLAMA_INSTALL_PATH}")
        version = setup.get_version()
        print(f"  ✓ Version: {version}")
    else:
        print(f"  ✗ Ollama not found at {setup.OLLAMA_INSTALL_PATH}")
        print("  → Download from: https://ollama.ai")
        return False
    
    # Check 2: API Connection
    print("\n[2] API Connection Check...")
    api_running = await setup.check_api_connection()
    if api_running:
        print(f"  ✓ Ollama API responding at {setup.OLLAMA_API_URL}")
    else:
        print(f"  ✗ Ollama API not responding at {setup.OLLAMA_API_URL}")
        print("  → Start Ollama: Open the Ollama app or run 'ollama serve'")
        return False
    
    # Check 3: Models
    print("\n[3] Downloaded Models Check...")
    models = await setup.get_models()
    if models:
        print(f"  ✓ Found {len(models)} model(s):")
        for model in models:
            print(f"    - {model}")
    else:
        print("  ⚠ No models downloaded yet")
        print("  → Download a model: ollama pull tinyllama")
        print("  → Download Phi-2: ollama pull phi")
        print("  → Download Mistral: ollama pull mistral")
    
    # Summary
    print("\n" + "=" * 70)
    if api_running:
        print("✓ OLLAMA SETUP COMPLETE - Ready for Week 2!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Download a model (if not already done):")
        print("   ollama pull tinyllama")
        print("   ollama pull phi")
        print("\n2. Start Week 2:")
        print("   uv run python verify_week_1.py  # Should work with live Ollama")
        print("\n3. Test streaming:")
        print("   uv run python example_week_1_usage.py")
        return True
    else:
        print("✗ OLLAMA NOT READY - Please fix issues above")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_ollama_setup())
    exit(0 if success else 1)
