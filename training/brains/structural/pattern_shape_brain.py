# training/brains/structural/pattern_shape_brain.py
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple
import random

from training.core.base_brain import BaseBrain
from config.game import DIA_DE_SORTE_RULES
from training.brains._utils import (
    UNIVERSO,
    build_faixas,
    count_even,
    max_consecutive_run,
    weighted_sample_without_replacement,
)

FAIXAS = build_faixas()


def _bucket_sum(total: int, size: int) -> str:
    # Buckets relativos à média esperada por tamanho
    media = ((DIA_DE_SORTE_RULES.universo_max + 1) / 2.0) * size
    if total < media * 0.85:
        return "sum_lt_85"
    if total < media * 0.95:
        return "sum_85_95"
    if total < media * 1.05:
        return "sum_95_105"
    if total < media * 1.15:
        return "sum_105_115"
    return "sum_ge_115"


def _band_counts(jogo: List[int]) -> Tuple[int, ...]:
    counts = [0 for _ in FAIXAS]
    for d in jogo:
        for idx, (a, b) in enumerate(FAIXAS):
            if a <= d <= b:
                counts[idx] += 1
                break
    return tuple(counts)


def _shape_key(jogo: List[int]) -> str:
    jogo = sorted(int(x) for x in jogo)
    ev = count_even(jogo)
    run = max_consecutive_run(jogo)
    bands = _band_counts(jogo)
    s = sum(jogo)
    band_tag = "-".join(str(x) for x in bands)
    return f"e{ev}_r{run}_b{band_tag}_{_bucket_sum(s, len(jogo))}"


class StructuralPatternShapeBrain(BaseBrain):
    """
    Cérebro Estrutural: aprende "shape" (forma) de jogos bons.
    - NÃO tenta prever dezenas específicas.
    - Aprende quais formatos aparecem mais quando o acerto é alto.
    - Gera jogos respeitando shapes prováveis, misturando exploração.
    """

    def __init__(self, db_conn, version: str = "v1"):
        super().__init__(
            db_conn=db_conn,
            brain_id="struct_shape",
            name="Structural - Pattern Shape",
            category="estrutural",
            version=version,
        )

        # contadores por shape, separados por faixa de pontos
        self.shape_4 = Counter()
        self.shape_5 = Counter()
        self.shape_6 = Counter()

        self.total_learns = 0

        self.load_state()
        self._rebuild_from_state()

    # --------------------------
    # BrainInterface
    # --------------------------
    def evaluate_context(self, context: Dict[str, Any]) -> float:
        # se ainda não aprendeu nada, relevância menor (mas não zero)
        learned = self.total_learns
        if learned <= 0:
            return 0.35
        if learned < 200:
            return 0.55
        return 0.75

    def generate(self, context: Dict[str, Any], size: int, n: int) -> List[List[int]]:
        size = int(size)
        n = int(n)
        size = max(DIA_DE_SORTE_RULES.jogo_min_dezenas, min(size, DIA_DE_SORTE_RULES.jogo_max_dezenas))

        # escolhe de qual “memória de shape” puxar
        # jogos maiores: foca mais em 6+; menores: 5+
        if size >= 13 and self.shape_6:
            source = self.shape_6
        elif self.shape_5:
            source = self.shape_5
        else:
            source = self.shape_4

        # se ainda vazio, gera aleatório com leve controle
        jogos: List[List[int]] = []
        if not source:
            for _ in range(n):
                jogos.append(sorted(random.sample(UNIVERSO, size)))
            return jogos

        # amostra shapes por peso
        keys = list(source.keys())
        weights = [max(1.0, float(source[k])) for k in keys]

        for _ in range(n):
            target = random.choices(keys, weights=weights, k=1)[0]
            jogo = self._generate_with_shape(target, size=size)
            jogos.append(sorted(jogo))

        return jogos

    def score_game(self, jogo: List[int], context: Dict[str, Any]) -> float:
        # score: quanto esse jogo “bate” com shapes premiados
        if not jogo:
            return 0.0
        k = _shape_key(jogo)

        s6 = float(self.shape_6.get(k, 0))
        s5 = float(self.shape_5.get(k, 0))
        s4 = float(self.shape_4.get(k, 0))

        # normalização simples (comparativo)
        denom = 1.0 + s4 + 1.5 * s5 + 2.5 * s6
        return (s4 + 1.5 * s5 + 2.5 * s6) / denom

    def learn(
        self,
        concurso_n: int,
        jogo: List[int],
        resultado_n1: List[int],
        pontos: int,
        context: Dict[str, Any],
    ) -> None:
        # aprende baseado no jogo que foi avaliado (candidato) + pontos obtidos no resultado real N+1
        if not jogo:
            return

        key = _shape_key(jogo)

        if pontos >= 6:
            self.shape_6[key] += 1
            self.shape_5[key] += 1
            self.shape_4[key] += 1
        elif pontos >= 5:
            self.shape_5[key] += 1
            self.shape_4[key] += 1
        elif pontos >= 4:
            self.shape_4[key] += 1

        self.total_learns += 1

        # performance por concurso (leve)
        self._perf_update(concurso=int(concurso_n), pontos=int(pontos), jogos_gerados=1)

        # autosave leve (micro-melhoria): salva a cada X learns
        # (o Hub também salva periodicamente, mas isso protege contra crash)
        if self.total_learns % 250 == 0:
            self.save_state()

    # --------------------------
    # Persistência
    # --------------------------
    def save_state(self) -> None:
        self.state = {
            "total_learns": int(self.total_learns),
            "shape_4": dict(self.shape_4),
            "shape_5": dict(self.shape_5),
            "shape_6": dict(self.shape_6),
        }
        super().save_state()

    def load_state(self) -> None:
        super().load_state()

    def _rebuild_from_state(self) -> None:
        try:
            self.total_learns = int(self.state.get("total_learns", 0))
            self.shape_4 = Counter(self.state.get("shape_4", {}) or {})
            self.shape_5 = Counter(self.state.get("shape_5", {}) or {})
            self.shape_6 = Counter(self.state.get("shape_6", {}) or {})
        except Exception:
            self.total_learns = 0
            self.shape_4 = Counter()
            self.shape_5 = Counter()
            self.shape_6 = Counter()

    def report(self) -> Dict[str, Any]:
        top6 = [k for k, _ in self.shape_6.most_common(5)]
        return {
            **super().report(),
            "total_learns": int(self.total_learns),
            "unique_shapes_4": len(self.shape_4),
            "unique_shapes_5": len(self.shape_5),
            "unique_shapes_6": len(self.shape_6),
            "top_shapes_6": top6,
        }

    # --------------------------
    # Geração por shape
    # --------------------------
    def _generate_with_shape(self, key: str, size: int) -> List[int]:
        """
        Interpreta o shape key e tenta montar um jogo que respeita:
        - evens
        - max_run
        - band counts
        - sum bucket (aproximado)
        """
        # parse simples
        # formato: e{ev}_r{run}_b{b1-b2-...}_{sum_bucket}
        parts = key.split("_")
        ev = int(parts[0][1:]) if parts and parts[0].startswith("e") else 7
        run = int(parts[1][1:]) if len(parts) > 1 and parts[1].startswith("r") else 3

        band = tuple(3 for _ in FAIXAS)  # default
        if len(parts) > 2 and parts[2].startswith("b"):
            b = parts[2][1:]
            try:
                band = tuple(int(x) for x in b.split("-"))
            except Exception:
                band = band

        # pools por faixa
        pools = [[x for x in UNIVERSO if faixa[0] <= x <= faixa[1]] for faixa in FAIXAS]

        jogo: List[int] = []

        # 1) respeita distribuição por faixas (se passar do tamanho, ajusta)
        target = list(band)
        if sum(target) != size:
            # ajusta proporcionalmente: mantém a “cara” mas encaixa no tamanho
            s = sum(target) if sum(target) > 0 else 1
            scaled = [max(0, int(round(size * (t / s)))) for t in target]
            # corrige diferença
            while sum(scaled) < size:
                scaled[scaled.index(max(scaled))] += 1
            while sum(scaled) > size:
                i = scaled.index(max(scaled))
                if scaled[i] > 0:
                    scaled[i] -= 1
                else:
                    break
            target = scaled

        for pool, k in zip(pools, target):
            if k <= 0:
                continue
            picks = random.sample(pool, min(k, len(pool)))
            jogo.extend(picks)

        # 2) se ainda faltou (por falta no pool), completa
        jogo = list(dict.fromkeys(jogo))  # remove duplicatas mantendo ordem
        while len(jogo) < size:
            x = random.choice(UNIVERSO)
            if x not in jogo:
                jogo.append(x)

        # 3) ajusta paridade (aproximado) via swaps
        jogo = sorted(jogo)
        for _ in range(20):
            cur_even = count_even(jogo)
            if cur_even == ev:
                break
            if cur_even < ev:
                # trocar um ímpar por par
                odds = [x for x in jogo if x % 2 == 1]
                evens_pool = [x for x in UNIVERSO if x % 2 == 0 and x not in jogo]
                if not odds or not evens_pool:
                    break
                jogo.remove(random.choice(odds))
                jogo.append(random.choice(evens_pool))
            else:
                # trocar um par por ímpar
                evens = [x for x in jogo if x % 2 == 0]
                odds_pool = [x for x in UNIVERSO if x % 2 == 1 and x not in jogo]
                if not evens or not odds_pool:
                    break
                jogo.remove(random.choice(evens))
                jogo.append(random.choice(odds_pool))
            jogo = sorted(jogo)

        # 4) evita sequência muito grande (run) com pequenos swaps
        for _ in range(25):
            if max_consecutive_run(jogo) <= run:
                break
            # remove um número do meio de uma sequência e substitui por outro distante
            candidates_remove = jogo[:]
            random.shuffle(candidates_remove)
            removed = None
            for r in candidates_remove:
                temp = [x for x in jogo if x != r]
                if max_consecutive_run(temp) < max_consecutive_run(jogo):
                    removed = r
                    jogo = temp
                    break
            if removed is None:
                break
            # adiciona um número fora do jogo e que não crie sequência grande
            pool = [x for x in UNIVERSO if x not in jogo]
            random.shuffle(pool)
            for x in pool:
                temp = sorted(jogo + [x])
                if max_consecutive_run(temp) <= run:
                    jogo = temp
                    break
            # garante tamanho
            while len(jogo) < size:
                x = random.choice([u for u in UNIVERSO if u not in jogo])
                jogo.append(x)
                jogo = sorted(jogo)

        return sorted(jogo)
