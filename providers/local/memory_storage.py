"""
Memory Storage System
Supports both JSON and SQLite backends for task/conversation history
"""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory"""

    CONVERSATION = "conversation"  # Chat history
    TASK = "task"  # Tasks and their results
    CONTEXT = "context"  # Current context/state
    INSIGHT = "insight"  # Learned patterns


@dataclass
class MemoryEntry:
    """Single memory entry"""

    id: str
    timestamp: str
    memory_type: str
    content: str
    metadata: dict[str, Any]
    tags: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class JSONMemory:
    """Simple JSON-based memory storage"""

    def __init__(self, storage_path: Path = None):
        """
        Initialize JSON memory storage

        Args:
            storage_path: Path to JSON file (default: ~/.jarvis_memory/memory.json)
        """
        self.storage_path = storage_path or (
            Path.home() / ".jarvis_memory" / "memory.json"
        )
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory: list[MemoryEntry] = []
        self._load()

    def _load(self):
        """Load memory from disk"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    self.memory = [MemoryEntry(**entry) for entry in data]
                logger.info(
                    f"Loaded {len(self.memory)} memory entries from {self.storage_path}"
                )
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                self.memory = []

    def _save(self):
        """Save memory to disk"""
        try:
            with open(self.storage_path, "w") as f:
                json.dump([entry.to_dict() for entry in self.memory], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def add_entry(
        self,
        memory_type: str,
        content: str,
        metadata: dict = None,
        tags: list[str] = None,
    ) -> str:
        """Add memory entry"""
        entry = MemoryEntry(
            id=datetime.now().isoformat(),
            timestamp=datetime.now().isoformat(),
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            tags=tags or [],
        )
        self.memory.append(entry)
        self._save()
        return entry.id

    def get_entries_by_type(self, memory_type: str) -> list[MemoryEntry]:
        """Get all entries of specific type"""
        return [e for e in self.memory if e.memory_type == memory_type]

    def get_entries_by_tag(self, tag: str) -> list[MemoryEntry]:
        """Get all entries with specific tag"""
        return [e for e in self.memory if tag in e.tags]

    def search(self, query: str) -> list[MemoryEntry]:
        """Search memory by content"""
        query_lower = query.lower()
        return [e for e in self.memory if query_lower in e.content.lower()]

    def get_recent(self, count: int = 10) -> list[MemoryEntry]:
        """Get most recent entries"""
        return sorted(self.memory, key=lambda x: x.timestamp, reverse=True)[:count]

    def clear(self):
        """Clear all memory"""
        self.memory = []
        self._save()


class SQLiteMemory:
    """SQLite-based memory storage with better querying"""

    def __init__(self, db_path: Path = None):
        """
        Initialize SQLite memory storage

        Args:
            db_path: Path to SQLite DB (default: ~/.jarvis_memory/memory.db)
        """
        self.db_path = db_path or (Path.home() / ".jarvis_memory" / "memory.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON memories(type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)
        """)

        conn.commit()
        conn.close()

    def add_entry(
        self,
        memory_type: str,
        content: str,
        metadata: dict = None,
        tags: list[str] = None,
    ) -> str:
        """Add memory entry"""
        entry_id = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO memories (id, timestamp, type, content, metadata, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                entry_id,
                datetime.now().isoformat(),
                memory_type,
                content,
                json.dumps(metadata or {}),
                json.dumps(tags or []),
            ),
        )

        conn.commit()
        conn.close()

        logger.info(f"Added memory entry: {entry_id}")
        return entry_id

    def get_entries_by_type(self, memory_type: str) -> list[dict]:
        """Get all entries of specific type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, timestamp, type, content, metadata, tags
            FROM memories
            WHERE type = ?
            ORDER BY timestamp DESC
        """,
            (memory_type,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "type": row[2],
                "content": row[3],
                "metadata": json.loads(row[4]),
                "tags": json.loads(row[5]),
            }
            for row in rows
        ]

    def get_entries_by_tag(self, tag: str) -> list[dict]:
        """Get all entries with specific tag"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, timestamp, type, content, metadata, tags
            FROM memories
            WHERE tags LIKE ?
            ORDER BY timestamp DESC
        """,
            (f'%"{tag}"%',),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "type": row[2],
                "content": row[3],
                "metadata": json.loads(row[4]),
                "tags": json.loads(row[5]),
            }
            for row in rows
        ]

    def search(self, query: str) -> list[dict]:
        """Full-text search in memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, timestamp, type, content, metadata, tags
            FROM memories
            WHERE content LIKE ?
            ORDER BY timestamp DESC
        """,
            (f"%{query}%",),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "type": row[2],
                "content": row[3],
                "metadata": json.loads(row[4]),
                "tags": json.loads(row[5]),
            }
            for row in rows
        ]

    def get_recent(self, count: int = 10) -> list[dict]:
        """Get most recent entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, timestamp, type, content, metadata, tags
            FROM memories
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (count,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "type": row[2],
                "content": row[3],
                "metadata": json.loads(row[4]),
                "tags": json.loads(row[5]),
            }
            for row in rows
        ]

    def get_conversation_history(self, limit: int = 50) -> list[dict]:
        """Get conversation history"""
        return self.get_entries_by_type(MemoryType.CONVERSATION.value)[:limit]

    def add_conversation(self, role: str, content: str, metadata: dict = None):
        """Add conversation turn"""
        self.add_entry(
            memory_type=MemoryType.CONVERSATION.value,
            content=f"{role}: {content}",
            metadata=metadata or {"role": role},
            tags=["conversation"],
        )

    def clear(self):
        """Clear all memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories")
        conn.commit()
        conn.close()

    def get_stats(self) -> dict:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM memories")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT type, COUNT(*) FROM memories GROUP BY type
        """)
        by_type = dict(cursor.fetchall())

        cursor.execute("""
            SELECT COUNT(DISTINCT tags) FROM memories
        """)
        total_tags = cursor.fetchone()[0]

        conn.close()

        return {
            "total_entries": total,
            "by_type": by_type,
            "total_tags": total_tags,
        }


class MemoryManager:
    """High-level memory management with backend abstraction"""

    def __init__(self, backend: str = "sqlite"):
        """
        Initialize memory manager

        Args:
            backend: 'sqlite' or 'json'
        """
        if backend == "sqlite":
            self.memory = SQLiteMemory()
        else:
            self.memory = JSONMemory()
        self.backend = backend

    def add_conversation_turn(self, role: str, content: str):
        """Add conversation turn to memory"""
        self.memory.add_entry(
            memory_type=MemoryType.CONVERSATION.value,
            content=f"{role}: {content}",
            tags=["conversation"],
            metadata={"role": role},
        )

    def add_task_result(self, task_name: str, result: str, success: bool):
        """Add task execution result to memory"""
        self.memory.add_entry(
            memory_type=MemoryType.TASK.value,
            content=result,
            tags=["task", task_name],
            metadata={"task": task_name, "success": success},
        )

    def get_context(self) -> str:
        """Get recent context for current session"""
        recent = self.memory.get_recent(20)
        context = "Recent context:\n\n"
        for entry in reversed(recent):
            if isinstance(entry, dict):
                context += f"[{entry['timestamp']}] {entry['content']}\n"
            else:
                context += f"[{entry.timestamp}] {entry.content}\n"
        return context

    def search_memory(self, query: str) -> str:
        """Search memory and return formatted results"""
        results = self.memory.search(query)
        if not results:
            return f"No memories found for: {query}"

        output = f"Found {len(results)} memory entries:\n\n"
        for result in results[:5]:
            if isinstance(result, dict):
                output += f"- {result['content']}\n"
            else:
                output += f"- {result.content}\n"
        return output
