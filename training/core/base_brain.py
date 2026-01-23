# training/core/base_brain.py
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from config.game import DIA_DE_SORTE_RULES
from training.core.brain_interface import BrainInterface

def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class BaseBrain(BrainInterface):
    def __init__(self, db_conn, brain_id: str, name: str, category: str, version: str = "1.0"):
        self.db = db_conn
        self.id = brain_id
        self.name = name
        self.category = category
        self.version = version
        self.enabled = True

        self._cerebro_pk: Optional[int] = None
        self.state: Dict[str, Any] = {}

        self._ensure_registered()

    def _ensure_registered(self) -> None:
        cur = self.db.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO cerebros (brain_id, nome, categoria, versao, habilitado, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            (self.id, self.name, self.category, self.version, now(), now())
        )
        self.db.commit()

        cur.execute("SELECT id, habilitado FROM cerebros WHERE brain_id = ?", (self.id,))
        row = cur.fetchone()
        if row:
            self._cerebro_pk = int(row[0])
            self.enabled = bool(int(row[1]))

    def save_state(self) -> None:
        if self._cerebro_pk is None:
            self._ensure_registered()

        cur = self.db.cursor()
        payload = json.dumps(self.state, ensure_ascii=False)

        cur.execute(
            """
            INSERT INTO cerebro_estado (cerebro_id, estado_json, atualizado_em)
            VALUES (?, ?, ?)
            ON CONFLICT(cerebro_id) DO UPDATE SET
                estado_json=excluded.estado_json,
                atualizado_em=excluded.atualizado_em
            """,
            (self._cerebro_pk, payload, now())
        )

        cur.execute(
            """
            UPDATE cerebros SET atualizado_em=?, versao=?, habilitado=?
            WHERE id=?
            """,
            (now(), self.version, 1 if self.enabled else 0, self._cerebro_pk)
        )
        self.db.commit()

    def load_state(self) -> None:
        if self._cerebro_pk is None:
            self._ensure_registered()

        cur = self.db.cursor()
        cur.execute("SELECT estado_json FROM cerebro_estado WHERE cerebro_id=?", (self._cerebro_pk,))
        row = cur.fetchone()
        if not row:
            self.state = {}
            return
        try:
            self.state = json.loads(row[0])
        except Exception:
            self.state = {}

    def _perf_update(self, concurso: int, pontos: int, jogos_gerados: int = 1) -> None:
        """registra performance por concurso (leve)"""
        if self._cerebro_pk is None:
            self._ensure_registered()

        cur = self.db.cursor()
        # busca existente
        tiers = DIA_DE_SORTE_RULES.performance_tiers
        col_names = ", ".join([f"qtd_{tier}" for tier in tiers])
        update_cols = ", ".join([f"qtd_{tier}=?" for tier in tiers])
        cur.execute(
            f"SELECT jogos_gerados, media_pontos, {col_names} FROM cerebro_performance WHERE cerebro_id=? AND concurso=?",
            (self._cerebro_pk, int(concurso))
        )
        row = cur.fetchone()

        if row:
            jg = int(row[0])
            media = float(row[1])
            qtds = [int(x) for x in row[2:]]
            jg = int(jg) + int(jogos_gerados)
            media = (float(media) * (jg - jogos_gerados) + pontos) / jg
            qtds = [
                qtd + (1 if pontos >= tier else 0)
                for qtd, tier in zip(qtds, tiers)
            ]

            update_sql = (
                "UPDATE cerebro_performance "
                f"SET jogos_gerados=?, media_pontos=?, {update_cols}, atualizado_em=? "
                "WHERE cerebro_id=? AND concurso=?"
            )
            cur.execute(update_sql, (jg, media, *qtds, now(), self._cerebro_pk, int(concurso)))
        else:
            insert_cols = ", ".join(
                ["cerebro_id", "concurso", "jogos_gerados", "media_pontos"] + [f"qtd_{tier}" for tier in tiers] + ["atualizado_em"]
            )
            placeholders = ",".join(["?"] * (4 + len(tiers) + 1))
            insert_sql = f"INSERT INTO cerebro_performance ({insert_cols}) VALUES ({placeholders})"
            cur.execute(
                insert_sql,
                (
                    self._cerebro_pk,
                    int(concurso),
                    int(jogos_gerados),
                    float(pontos),
                    *[
                        1 if pontos >= tier else 0
                        for tier in tiers
                    ],
                    now(),
                ),
            )
        self.db.commit()

    def report(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "enabled": self.enabled,
            "state_keys": sorted(list(self.state.keys()))
        }
