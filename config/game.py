from __future__ import annotations

from dataclasses import dataclass
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

MESES_SORTE_MAP: Dict[str, int] = {mes.lower(): idx + 1 for idx, mes in enumerate(MESES_SORTE)}
