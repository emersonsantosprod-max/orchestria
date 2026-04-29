---
name: python-patterns
description: >
  Python-specific patterns: Protocols, dataclasses, context managers,
  decorators, async/await, type hints and package organization. Use when
  writing or reviewing Python code to apply Pythonic idioms.
paths:
  - "app/**/*.py"
  - "ui/**/*.py"
  - "tests/**/*.py"
---

# Python Patterns

## Protocol (Duck Typing)

Structural subtyping — type hints without inheritance:

```python
from typing import Protocol

class Repository(Protocol):
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...

class UserRepository:
    def find_by_id(self, id: str) -> dict | None:
        pass

    def save(self, entity: dict) -> dict:
        pass
```

## Dataclasses as DTOs

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CreateUserRequest:
    name: str
    email: str
    age: Optional[int] = None
    tags: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str
```

## Context Managers

```python
from contextlib import contextmanager

@contextmanager
def database_transaction(db):
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise
```

## Generators

```python
def read_large_file(filename: str):
    with open(filename, 'r') as f:
        for line in f:
            yield line.strip()
```

## Decorators

```python
from functools import wraps
import time

def timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.2f}s")
        return result
    return wrapper
```

## Async/Await

```python
import asyncio

async def fetch_user(user_id: str) -> dict:
    await asyncio.sleep(0.1)
    return {"id": user_id, "name": "Alice"}

async def fetch_all_users(user_ids: list[str]) -> list[dict]:
    tasks = [fetch_user(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)
```

## Type Hints

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T]):
    def find_by_id(self, id: str) -> T | None:
        pass

# Union types (Python 3.10+)
def process(value: str | int | None) -> str:
    match value:
        case str():
            return value.upper()
        case int():
            return str(value)
        case None:
            return "empty"
```

## Dependency Injection

```python
class UserService:
    def __init__(
        self,
        repository: Repository,
        cache: Cache | None = None
    ):
        self.repository = repository
        self.cache = cache
```

## Error Handling

```python
class DomainError(Exception):
    pass

class UserNotFoundError(DomainError):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")
```

## Functional Programming

```python
from functools import reduce

def pipe(*functions):
    def inner(arg):
        return reduce(lambda x, f: f(x), functions, arg)
    return inner

process = pipe(str.strip, str.lower, lambda s: s.replace(' ', '_'))
result = process("  Hello World  ")  # "hello_world"
```

## Property Decorators

```python
class User:
    def __init__(self, name: str):
        self._name = name
        self._email = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str | None:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if '@' not in value:
            raise ValueError("Invalid email")
        self._email = value
```
