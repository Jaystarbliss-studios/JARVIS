"""
PHASE 1 Verification Script
Checks that all components are properly installed and working
"""

import sys
import subprocess
from pathlib import Path
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            console.print(f"[green]✓ Ollama installed: {version}[/green]")
            return True
    except Exception:
        pass
    
    console.print("[red]✗ Ollama not installed[/red]")
    console.print("  Download: https://ollama.ai/download")
    return False


def check_ollama_running():
    """Check if Ollama server is running"""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            console.print("[green]✓ Ollama server running[/green]")
            return True
    except Exception:
        pass
    
    console.print("[red]✗ Ollama server not running[/red]")
    console.print("  Start: ollama serve (or restart after install)")
    return False


def check_ollama_models():
    """Check available Ollama models"""
    try:
        import httpx
        import json
        response = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            
            if not models:
                console.print("[yellow]⚠ No models downloaded[/yellow]")
                console.print("  Run: ollama pull mistral")
                return False
            
            table = Table(title="Available Models")
            table.add_column("Name", style="cyan")
            table.add_column("Size (GB)")
            
            for model in models:
                size_gb = model.get("size", 0) / (1024 ** 3)
                table.add_row(model["name"], f"{size_gb:.2f}")
            
            console.print(table)
            return len(models) > 0
    except Exception as e:
        console.print(f"[red]✗ Could not check models: {e}[/red]")
        return False


def check_python_dependencies():
    """Check required Python packages"""
    required = {
        "httpx": "HTTP client",
        "click": "CLI framework",
        "rich": "Terminal UI",
        "pydantic": "Data validation",
    }
    
    missing = []
    
    for package, desc in required.items():
        try:
            __import__(package)
            console.print(f"[green]✓ {package}[/green] ({desc})")
        except ImportError:
            console.print(f"[red]✗ {package}[/red] ({desc})")
            missing.append(package)
    
    if missing:
        console.print(f"\n[yellow]Install missing packages:[/yellow]")
        console.print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def check_local_provider_module():
    """Check if local provider module exists"""
    local_dir = Path(__file__).parent / "providers" / "local"
    
    required_files = [
        "__init__.py",
        "ollama_engine.py",
        "memory_storage.py",
        "cli.py",
    ]
    
    for filename in required_files:
        filepath = local_dir / filename
        if filepath.exists():
            console.print(f"[green]✓ {filename}[/green]")
        else:
            console.print(f"[red]✗ {filename}[/red]")
            return False
    
    return True


def check_memory_storage():
    """Check memory storage initialization"""
    try:
        from providers.local.memory_storage import MemoryManager
        
        manager = MemoryManager(backend="sqlite")
        manager.add_conversation_turn("verification", "test")
        
        console.print("[green]✓ Memory storage working[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Memory storage error: {e}[/red]")
        return False


async def check_ollama_connection():
    """Test Ollama connection"""
    try:
        from providers.local.ollama_engine import OllamaEngine
        
        engine = OllamaEngine()
        connected = await engine.check_connection()
        
        if connected:
            console.print("[green]✓ Ollama connection verified[/green]")
        else:
            console.print("[red]✗ Ollama connection failed[/red]")
        
        await engine.close()
        return connected
    except Exception as e:
        console.print(f"[red]✗ Connection test error: {e}[/red]")
        return False


async def check_model_inference():
    """Test model inference"""
    try:
        from providers.local.ollama_engine import OllamaEngine
        
        engine = OllamaEngine("mistral")
        
        # Quick inference test
        response = ""
        async for token in engine.stream_response(
            "Say 'Hello' in one word",
            temperature=0.1
        ):
            response += token
        
        if response.strip():
            console.print(f"[green]✓ Model inference working[/green]")
            console.print(f"  Response: {response[:50]}...")
            await engine.close()
            return True
    except Exception as e:
        console.print(f"[red]✗ Model inference error: {e}[/red]")
        return False


def run_all_checks():
    """Run all verification checks"""
    console.print(Panel(
        "[cyan]PHASE 1 Verification[/cyan]\n"
        "Checking installation and configuration",
        title="🔍 System Check"
    ))
    
    console.print("\n[cyan]═ Ollama Installation ═[/cyan]\n")
    check1 = check_ollama_installed()
    
    console.print("\n[cyan]═ Ollama Server ═[/cyan]\n")
    check2 = check_ollama_running()
    
    console.print("\n[cyan]═ Models ═[/cyan]\n")
    check3 = check_ollama_models()
    
    console.print("\n[cyan]═ Python Dependencies ═[/cyan]\n")
    check4 = check_python_dependencies()
    
    console.print("\n[cyan]═ Local Provider Module ═[/cyan]\n")
    check5 = check_local_provider_module()
    
    console.print("\n[cyan]═ Memory Storage ═[/cyan]\n")
    check6 = check_memory_storage()
    
    console.print("\n[cyan]═ Ollama Connection ═[/cyan]\n")
    check7 = asyncio.run(check_ollama_connection())
    
    console.print("\n[cyan]═ Model Inference ═[/cyan]\n")
    if check7:
        check8 = asyncio.run(check_model_inference())
    else:
        console.print("[yellow]⏭️  Skipping inference test (server not connected)[/yellow]")
        check8 = None
    
    # Summary
    console.print("\n[cyan]═ Summary ═[/cyan]\n")
    
    checks = {
        "Ollama Installed": check1,
        "Ollama Server": check2,
        "Models Available": check3,
        "Python Deps": check4,
        "Local Module": check5,
        "Memory Storage": check6,
        "Connection": check7,
        "Inference": check8,
    }
    
    passed = sum(1 for v in checks.values() if v is True)
    total = sum(1 for v in checks.values() if v is not None)
    
    table = Table(title="Verification Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    
    for check, result in checks.items():
        if result is None:
            status = "[yellow]Skipped[/yellow]"
        elif result:
            status = "[green]✓ Pass[/green]"
        else:
            status = "[red]✗ Fail[/red]"
        table.add_row(check, status)
    
    console.print(table)
    
    if check8 is False or (check2 or check7):
        console.print(f"\n[bold]{passed}/{total} checks passed[/bold]")
        if passed == total:
            console.print("\n[green]✓ All systems ready! Run:[/green]")
            console.print("  [cyan]python providers/local/cli.py chat[/cyan]")
        else:
            console.print("\n[yellow]⚠ Some checks failed[/yellow]")
            console.print("See failures above and consult PHASE_1_SETUP.md")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
