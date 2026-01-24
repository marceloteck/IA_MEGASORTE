from __future__ import annotations

from dataclasses import dataclass
import html
import unicodedata
from typing import Dict, List


@dataclass(frozen=True)
class GameRules:
    nome: str
    universo_max: int
    jogo_min_dezenas: int
    jogo_max_dezenas: int
    resultado_dezenas: int
    grid_cols: int
    performance_tiers: tuple[int, ...]
    bonus_tiers: tuple[int, ...]
    memoria_min_acertos: int

    @property
    def universo(self) -> List[int]:
        return list(range(1, self.universo_max + 1))

    @property
    def grid_rows(self) -> int:
        return (self.universo_max + self.grid_cols - 1) // self.grid_cols

    @property
    def low_number_max(self) -> int:
        return self.universo_max // 2


DIA_DE_SORTE_RULES = GameRules(
    nome="Dia de Sorte",
    universo_max=31,
    jogo_min_dezenas=7,
    jogo_max_dezenas=15,
    resultado_dezenas=7,
    grid_cols=5,
    performance_tiers=(4, 5, 6, 7),
    bonus_tiers=(6, 7),
    memoria_min_acertos=5,
)

MESES_SORTE = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]

def _normalize_mes_key(value: str) -> str:
    text = html.unescape(value).strip().lower()
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


MESES_SORTE_MAP: Dict[str, int] = {
    _normalize_mes_key(mes): idx + 1 for idx, mes in enumerate(MESES_SORTE)
}


def normalize_mes_sorte(value: object) -> int | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        mes_num = int(text)
    except ValueError:
        mes_num = None

    if mes_num is not None:
        return mes_num if 1 <= mes_num <= 12 else None

    normalized = _normalize_mes_key(text)
    return MESES_SORTE_MAP.get(normalized)
