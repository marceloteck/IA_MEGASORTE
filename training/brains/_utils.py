# training/brains/_utils.py
from __future__ import annotations
import random
from typing import Dict, List, Sequence

from config.game import DIA_DE_SORTE_RULES

UNIVERSO = DIA_DE_SORTE_RULES.universo
UNIVERSO_MAX = DIA_DE_SORTE_RULES.universo_max
GRID_COLS = DIA_DE_SORTE_RULES.grid_cols
GRID_ROWS = DIA_DE_SORTE_RULES.grid_rows

def weighted_sample_without_replacement(weights: Dict[int, float], k: int) -> List[int]:
    # método simples e leve: amostra repetida sem reposição
    pool = UNIVERSO[:]
    result = []
    for _ in range(k):
        w = [max(0.0001, float(weights.get(x, 0.001))) for x in pool]
        pick = random.choices(pool, weights=w, k=1)[0]
        result.append(pick)
        pool.remove(pick)
    return sorted(result)

def count_even(jogo: List[int]) -> int:
    return sum(1 for x in jogo if x % 2 == 0)

def max_consecutive_run(jogo: List[int]) -> int:
    s = sorted(jogo)
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i-1] + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best

def build_faixas(step: int = 5) -> List[tuple[int, int]]:
    faixas: List[tuple[int, int]] = []
    start = 1
    while start <= UNIVERSO_MAX:
        end = min(UNIVERSO_MAX, start + step - 1)
        faixas.append((start, end))
        start = end + 1
    return faixas

def build_moldura() -> set[int]:
    moldura: set[int] = set()
    for value in range(1, UNIVERSO_MAX + 1):
        idx = value - 1
        row = idx // GRID_COLS
        col = idx % GRID_COLS
        if row == 0 or row == GRID_ROWS - 1 or col == 0 or col == GRID_COLS - 1:
            moldura.add(value)
    return moldura

def primes_up_to(max_value: int) -> set[int]:
    primes: set[int] = set()
    for num in range(2, max_value + 1):
        is_prime = True
        for div in range(2, int(num ** 0.5) + 1):
            if num % div == 0:
                is_prime = False
                break
        if is_prime:
            primes.add(num)
    return primes

def fibonacci_up_to(max_value: int) -> set[int]:
    fibs: set[int] = set()
    a, b = 1, 2
    fibs.add(1)
    while b <= max_value:
        fibs.add(b)
        a, b = b, a + b
    return fibs

def multiples_of(n: int, max_value: int) -> set[int]:
    return {x for x in range(n, max_value + 1, n)}
