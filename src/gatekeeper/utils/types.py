from __future__ import annotations

from collections.abc import Callable

from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Decision

PolicyRule = Callable[[Finding], Decision | None]

PolicyResult = tuple[Finding, Decision]

PolicyResults = list[PolicyResult]
