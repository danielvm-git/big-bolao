"""Maquina de estados do fluxo de palpite.

Concentra a (de)serializacao de callback_data e a validacao de transicoes
de passo. Os tres handlers em handlers.py consomem este modulo em vez de
implementar split() cada um com seu proprio formato.

Callback data format:
  g|<match_id>          → ESCOLHER_JOGO
  h|<match_id>|<gols>    → GOLS_CASA
  f|<match_id>|<gc>|<gf> → GOLS_FORA
"""
from __future__ import annotations

from enum import Enum, auto


class Step(Enum):
    """Cada passo do fluxo de palpite."""
    ESCOLHER_JOGO = auto()
    GOLS_CASA = auto()
    GOLS_FORA = auto()


# Mapa de prefixo → Step
_PREFIX_MAP: dict[str, Step] = {
    "g": Step.ESCOLHER_JOGO,
    "h": Step.GOLS_CASA,
    "f": Step.GOLS_FORA,
}

# Transicoes validas: (de, para)
_VALID_TRANSITIONS: set[tuple[Step, Step]] = {
    (Step.ESCOLHER_JOGO, Step.GOLS_CASA),
    (Step.GOLS_CASA, Step.GOLS_FORA),
}


class BettingFlow:
    """Ponto unico de (de)serializacao e validacao do fluxo de palpite."""

    @staticmethod
    def serialize(step: Step, **params: str | int) -> str:
        """Produz callback_data string a partir de um passo + parametros.

        Exemplo:
          BettingFlow.serialize(Step.ESCOLHER_JOGO, match_id="R1-01") -> "g|R1-01"
          BettingFlow.serialize(Step.GOLS_CASA, match_id="R1-01", gols=3) -> "h|R1-01|3"
          BettingFlow.serialize(Step.GOLS_FORA, match_id="R1-01", gc=2, gf=1) -> "f|R1-01|2|1"
        """
        prefix = _step_to_prefix(step)
        parts = [prefix]

        if step == Step.ESCOLHER_JOGO:
            parts.append(str(params["match_id"]))
        elif step == Step.GOLS_CASA:
            parts.append(str(params["match_id"]))
            parts.append(str(params["gols"]))
        elif step == Step.GOLS_FORA:
            parts.append(str(params["match_id"]))
            parts.append(str(params["gc"]))
            parts.append(str(params["gf"]))

        return "|".join(parts)

    @staticmethod
    def deserialize(data: str) -> tuple[Step, dict] | None:
        """Parseia callback_data string de volta para (Step, dict) ou None se invalido.

        Os valores numericos (gols, gc, gf) sao convertidos para int.
        """
        if not data:
            return None
        parts = data.split("|")
        prefix = parts[0]
        step = _PREFIX_MAP.get(prefix)
        if step is None:
            return None

        if step == Step.ESCOLHER_JOGO:
            if len(parts) != 2:
                return None
            return step, {"match_id": parts[1]}

        if step == Step.GOLS_CASA:
            if len(parts) != 3:
                return None
            try:
                gols = int(parts[2])
            except ValueError:
                return None
            return step, {"match_id": parts[1], "gols": gols}

        if step == Step.GOLS_FORA:
            if len(parts) != 4:
                return None
            try:
                gc = int(parts[2])
                gf = int(parts[3])
            except ValueError:
                return None
            return step, {"match_id": parts[1], "gc": gc, "gf": gf}

        return None

    @staticmethod
    def validate_transition(current: Step, next_step: Step) -> None:
        """Levanta ValueError se a transicao nao for valida."""
        if (current, next_step) not in _VALID_TRANSITIONS:
            raise ValueError(
                f"invalid transition: {current.name} -> {next_step.name}")

    @staticmethod
    def pattern_for(step: Step) -> str:
        """Retorna regex pattern para registrar CallbackQueryHandler em bot.py."""
        prefix = _step_to_prefix(step)
        return rf"^{prefix}\|"


def _step_to_prefix(step: Step) -> str:
    for prefix, s in _PREFIX_MAP.items():
        if s == step:
            return prefix
    raise ValueError(f"unknown step: {step}")
