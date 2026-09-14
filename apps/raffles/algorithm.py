"""
Núcleo do algoritmo de sorteio — funções puras, sem ORM.

Separado do models.py para facilitar testes unitários sem banco de dados.
"""

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CommentEntry:
    username: str
    text: str
    ig_comment_id: str
    commented_at: datetime
    is_reply: bool = False
    parent_ig_id: str = ""


def count_distinct_mentions(text: str, author_username: str) -> int:
    """
    Conta @menções distintas em um texto, excluindo o próprio autor.
    Ignora pontuação ao final da palavra.
    """
    mentions: set[str] = set()
    for word in text.split():
        if word.startswith("@"):
            handle = word.lstrip("@").rstrip(".,!?;:").lower()
            if handle and handle != author_username.lower():
                mentions.add(handle)
    return len(mentions)


def filter_entries(
    entries: list[CommentEntry],
    *,
    include_replies: bool,
    owner_username: str,
    exclude_owner: bool,
    excluded_usernames: list[str],
    comments_until: Optional[datetime],
    required_keyword: str,
    min_mentions: int,
    unique_per_user: bool,
) -> list[CommentEntry]:
    """
    Aplica as regras do sorteio e retorna a lista de participantes válidos,
    ordenados deterministicamente por (commented_at, ig_comment_id).
    """
    result = list(entries)

    if not include_replies:
        result = [e for e in result if not e.is_reply]

    if exclude_owner and owner_username:
        result = [e for e in result if e.username.lower() != owner_username.lower()]

    excluded_lower = {u.lower() for u in excluded_usernames}
    result = [e for e in result if e.username.lower() not in excluded_lower]

    if comments_until is not None:
        result = [e for e in result if e.commented_at <= comments_until]

    if required_keyword:
        kw = required_keyword.lower()
        result = [e for e in result if kw in e.text.lower()]

    if min_mentions > 0:
        result = [
            e for e in result
            if count_distinct_mentions(e.text, e.username) >= min_mentions
        ]

    # Ordenação determinística antes de aplicar unique_per_user
    result.sort(key=lambda e: (e.commented_at, e.ig_comment_id))

    if unique_per_user:
        seen: set[str] = set()
        unique: list[CommentEntry] = []
        for entry in result:
            key = entry.username.lower()
            if key not in seen:
                seen.add(key)
                unique.append(entry)
        result = unique

    return result


def compute_participants_hash(participants: list[CommentEntry]) -> str:
    """
    SHA-256 da lista de participantes válidos (para auditoria no certificado).
    A lista deve estar ordenada deterministicamente antes de chamar esta função.
    """
    data = json.dumps(
        [{"username": c.username, "comment_id": c.ig_comment_id} for c in participants],
        ensure_ascii=False,
    )
    return hashlib.sha256(data.encode()).hexdigest()


def sample_winners(
    participants: list[CommentEntry],
    winners_count: int,
    alternates_count: int,
) -> tuple[list[CommentEntry], list[CommentEntry]]:
    """
    Sorteia ganhadores e suplentes usando secrets.SystemRandom (CSPRNG).
    Retorna (ganhadores, suplentes). Sem repetição de usuários.
    """
    total = winners_count + alternates_count
    pick = min(total, len(participants))
    chosen = secrets.SystemRandom().sample(participants, pick)
    return chosen[:winners_count], chosen[winners_count:]
