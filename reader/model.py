from dataclasses import dataclass, field


@dataclass
class Block:
    source: str
    text: str
    kind: str = 'p'
    id: str = ''
    spans: list[tuple[int, int, str]] = field(default_factory=list)


@dataclass
class Book:
    identity: str
    title: str
    format: str
    blocks: list[Block]
    toc: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Unsupported(ValueError):
    pass
