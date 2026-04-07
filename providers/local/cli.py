"""
Local Model Command Interface
Interactive CLI for voice-free interaction with local models
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from providers.local.ollama_engine import OllamaEngine, ModelSize
from providers.local.memory_storage import MemoryManager, MemoryType

console = Console()


class LocalCommandInterface:
    """Interactive command interface for local models"""
    
    def __init__(self, model_name: str = "mistral"):
        self.model_name = model_name
        self.ollama: Optional[OllamaEngine] = None
        self.memory = MemoryManager(backend="sqlite")
        self.running = False
        self.history = []
    
    async def init(self) -> bool:
        """Initialize Ollama engine"""
        try:
            self.ollama = OllamaEngine(self.model_name)
            
            # Check connection
            if not await self.ollama.check_connection():
                console.print(
                    "[red]✗ Ollama server not running[/red]",
                    style="bold"
                )
                console.print("Start Ollama with: ollama serve")
                return False
            
            console.print("[green]✓ Connected to Ollama[/green]")
            
            # Check if model is available
            models = await self.ollama.list_models()
            available_models = [m["name"] for m in models]
            
            if self.model_name not in available_models:
                console.print(f"\n[yellow]Model '{self.model_name}' not found[/yellow]")
                console.print(f"Available models: {', '.join(available_models)}")
                console.print(f"\nDownloading {self.model_name}...")
                success = await self.ollama.pull_model(self.model_name)
                if not success:
                    return False
            
            console.print(f"[green]✓ Model ready: {self.model_name}[/green]\n")
            return True
        
        except Exception as e:
            console.print(f"[red]Initialization error: {e}[/red]")
            return False
    
    async def chat_mode(self):
        """Interactive chat mode"""
        console.print(Panel(
            "[cyan]Local Model Chat Interface[/cyan]\n"
            "Type 'help' for commands\n"
            "Type 'exit' to quit",
            title="💬 Chat Mode"
        ))
        
        self.running = True
        messages = []
        
        while self.running:
            try:
                user_input = console.input("[cyan]You:[/cyan] ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "exit":
                    self.running = False
                    break
                
                if user_input.lower() == "help":
                    self._show_help()
                    continue
                
                if user_input.lower() == "history":
                    self._show_history()
                    continue
                
                if user_input.lower() == "clear":
                    messages = []
                    console.print("[yellow]Conversation cleared[/yellow]")
                    continue
                
                if user_input.lower() == "memory":
                    self._show_memory_stats()
                    continue
                
                # Add to messages
                messages.append({"role": "user", "content": user_input})
                self.memory.add_conversation_turn("user", user_input)
                
                # Generate response
                console.print("[cyan]Assistant:[/cyan] ", end="", flush=True)
                response = ""
                
                async for token in self.ollama.stream_response(
                    self._format_messages(messages)
                ):
                    console.print(token, end="", flush=True)
                    response += token
                
                console.print("\n")
                
                messages.append({"role": "assistant", "content": response})
                self.memory.add_conversation_turn("assistant", response)
                self.history.append({
                    "user": user_input,
                    "assistant": response
                })
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    async def command_mode(self, command: str):
        """Execute single command"""
        try:
            console.print(f"[cyan]Query:[/cyan] {command}\n")
            console.print("[cyan]Response:[/cyan]\n")
            
            async for token in self.ollama.stream_response(command):
                console.print(token, end="", flush=True)
            
            console.print("\n")
            self.memory.add_conversation_turn("user", command)
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    async def code_mode(self, task: str):
        """Code generation mode"""
        prompt = f"""You are an expert software engineer. Generate clean, well-documented code for the following task:

Task: {task}

Requirements:
- Write production-ready code
- Include docstrings and comments
- Handle errors gracefully
- Use best practices

Code:"""
        
        console.print(Panel(task, title="📝 Code Generation Task"))
        console.print("[cyan]Generated Code:[/cyan]\n")
        
        code = ""
        async for token in self.ollama.stream_response(prompt, temperature=0.3):
            console.print(token, end="", flush=True)
            code += token
        
        console.print("\n")
        self.memory.add_task_result(
            task_name="code_generation",
            result=code,
            success=True
        )
    
    async def analysis_mode(self, code: str):
        """Code analysis mode"""
        prompt = f"""Analyze the following code and provide:
1. What it does
2. Potential issues
3. Suggestions for improvement
4. Security considerations (if applicable)

Code:
```
{code}
```

Analysis:"""
        
        console.print("[cyan]Analyzing code...[/cyan]\n")
        
        async for token in self.ollama.stream_response(prompt, temperature=0.3):
            console.print(token, end="", flush=True)
        
        console.print("\n")
    
    def _format_messages(self, messages: list) -> str:
        """Format messages for model input"""
        formatted = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['content']}\n\n"
        formatted += "Assistant:"
        return formatted
    
    def _show_help(self):
        """Show help information"""
        help_text = """
Commands:
  exit       - Exit chat mode
  clear      - Clear conversation history
  history    - Show conversation history
  memory     - Show memory statistics
  help       - Show this help

Chat naturally for multi-turn conversations.
        """
        console.print(Panel(help_text, title="Help"))
    
    def _show_history(self):
        """Show conversation history"""
        if not self.history:
            console.print("[yellow]No conversation history[/yellow]")
            return
        
        table = Table(title="Conversation History")
        table.add_column("Turn", style="cyan")
        table.add_column("User Input")
        table.add_column("Response")
        
        for i, turn in enumerate(self.history[-5:], 1):
            table.add_row(
                str(i),
                turn["user"][:50] + "..." if len(turn["user"]) > 50 else turn["user"],
                turn["assistant"][:50] + "..." if len(turn["assistant"]) > 50 else turn["assistant"]
            )
        
        console.print(table)
    
    def _show_memory_stats(self):
        """Show memory statistics"""
        if isinstance(self.memory.memory, object) and hasattr(self.memory.memory, 'get_stats'):
            stats = self.memory.memory.get_stats()
            console.print(Panel(
                f"Total entries: {stats['total_entries']}\n"
                f"By type: {stats['by_type']}\n"
                f"Memory size: {stats['total_tags']} tags",
                title="📝 Memory Stats"
            ))
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.ollama:
            await self.ollama.close()


@click.group()
def cli():
    """Local Model Command Interface - Interact with Ollama models"""
    pass


@cli.command()
@click.option("--model", default="mistral", help="Model to use (default: mistral)")
def chat(model):
    """Start interactive chat mode"""
    interface = LocalCommandInterface(model)
    
    async def main():
        if await interface.init():
            await interface.chat_mode()
        await interface.cleanup()
    
    asyncio.run(main())


@cli.command()
@click.argument("query")
@click.option("--model", default="mistral", help="Model to use")
def ask(query, model):
    """Ask a single question"""
    interface = LocalCommandInterface(model)
    
    async def main():
        if await interface.init():
            await interface.command_mode(query)
        await interface.cleanup()
    
    asyncio.run(main())


@cli.command()
@click.argument("task")
@click.option("--model", default="mistral", help="Model to use")
def generate(task, model):
    """Generate code for a task"""
    interface = LocalCommandInterface(model)
    
    async def main():
        if await interface.init():
            await interface.code_mode(task)
        await interface.cleanup()
    
    asyncio.run(main())


@cli.command()
@click.argument("filename")
@click.option("--model", default="mistral", help="Model to use")
def analyze(filename, model):
    """Analyze code from a file"""
    interface = LocalCommandInterface(model)
    
    async def main():
        try:
            with open(filename, 'r') as f:
                code = f.read()
            if await interface.init():
                await interface.analysis_mode(code)
        except FileNotFoundError:
            console.print(f"[red]File not found: {filename}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        finally:
            await interface.cleanup()
    
    asyncio.run(main())


@cli.command()
@click.option("--model", default="mistral", help="Model to use")
def list_models(model):
    """List available Ollama models"""
    interface = LocalCommandInterface(model)
    
    async def main():
        if await interface.init():
            models = await interface.ollama.list_models()
            
            table = Table(title="Available Models")
            table.add_column("Name", style="cyan")
            table.add_column("Size")
            table.add_column("Modified")
            
            for m in models:
                table.add_row(m["name"], f"{m['size'] / (1024**3):.2f}GB", m.get("modified_at", "N/A")[:10])
            
            console.print(table)
        await interface.cleanup()
    
    asyncio.run(main())


@cli.command()
@click.argument("model_name")
def download(model_name):
    """Download a model from Ollama registry"""
    interface = LocalCommandInterface(model_name)
    
    async def main():
        if await interface.init():
            console.print(f"\n[cyan]Downloading {model_name}...[/cyan]")
            success = await interface.ollama.pull_model(model_name)
            if success:
                console.print(f"[green]✓ {model_name} ready to use[/green]")
            else:
                console.print(f"[red]✗ Failed to download {model_name}[/red]")
        await interface.cleanup()
    
    asyncio.run(main())


if __name__ == "__main__":
    cli()
