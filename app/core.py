"""
core.py — contratos e utilitários compartilhados do pipeline.

Conteúdo:
  - Normalização (matrícula, data, desconto em minutos ↔ HH:MM)
  - Parse de data → objeto date
  - Deduplicação de observação (cópia bit-exata da antiga montar_observacao)
  - Dataclasses Update e Inconsistencia (contratos estritos)
  - Factory inconsistencia() com origem obrigatória

Invariantes:
  - Update.tipo ∈ {'treinamento','ferias','atestado'}
  - Inconsistencia.origem ∈ {'treinamento','ferias','atestado','writer'} (sem default)
  - situacao só é permitida para tipo='ferias' ou tipo='atestado'
  - Update e Inconsistencia expõem acesso dict-like (get/__getitem__) como
    camada transitória para consumidores legados. Remover em cleanup.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Regexes compartilhadas
# ---------------------------------------------------------------------------

_RE_DDMMYYYY = re.compile(r'\d{2}/\d{2}/\d{4}$')
_RE_HHMMSS   = re.compile(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$')


# ---------------------------------------------------------------------------
# Normalização
# ---------------------------------------------------------------------------

def normalizar_matricula(valor) -> str:
    """
    Unifica matrícula em formato canônico (RE bare e Chapa com prefixo).

    Regra: pega o trecho após o último '.' e remove zeros à esquerda.
      "00012345" → "12345"
      "1.095585" → "95585"
    """
    if valor is None:
        return ''
    return str(valor).strip().split('.')[-1].lstrip('0')


def normalizar_data(valor) -> str:
    """Normaliza data para 'dd/mm/aaaa'. Retorna string original se não parseável."""
    if hasattr(valor, 'strftime'):
        return valor.strftime('%d/%m/%Y')
    s = str(valor).strip()
    if _RE_DDMMYYYY.match(s):
        return s
    try:
        return datetime.strptime(s, '%d/%m/%Y').strftime('%d/%m/%Y')
    except ValueError:
        return s


def parse_data_obj(valor):
    """Converte data (datetime ou 'dd/mm/aaaa') em date. Retorna None se inválido."""
    if valor is None:
        return None
    if hasattr(valor, 'date') and not isinstance(valor, str):
        try:
            return valor.date()
        except Exception:
            pass
    s = str(valor).strip()
    try:
        return datetime.strptime(s, '%d/%m/%Y').date()
    except (ValueError, TypeError):
        return None


def converter_desconto_para_minutos(valor) -> int:
    """Aceita None, '', 'HH:MM', 'HH:MM:SS', datetime.time. Inválido → 0."""
    if valor is None or valor == '':
        return 0
    if hasattr(valor, 'hour') and hasattr(valor, 'minute'):
        return valor.hour * 60 + valor.minute
    if isinstance(valor, str):
        s = valor.strip()
        if not s:
            return 0
        match = _RE_HHMMSS.match(s)
        if match:
            return int(match.group(1)) * 60 + int(match.group(2))
        return 0
    return 0


def converter_minutos_para_hhmmss(minutos: int) -> str:
    """Ex: 75 → '01:15', 0 → '00:00'."""
    hh = minutos // 60
    mm = minutos % 60
    return f"{hh:02d}:{mm:02d}"


# ---------------------------------------------------------------------------
# Deduplicação de observação
#
# Cópia bit-exata da antiga treinamento.montar_observacao:
#   - split em ';' (sem espaço)
#   - strip de cada parte; descarta vazias
#   - set para lookup O(1); list preserva ordem de inserção
#   - join com '; '
#
# Qualquer mudança de semântica aqui é regressão. test_integration.py:42 é o
# guard canônico (compara bytes exatos da célula).
# ---------------------------------------------------------------------------

def deduplicar_observacao(observacao_existente, novas_entradas: list) -> str:
    obs = observacao_existente or ''
    partes = [p.strip() for p in obs.split(';') if p.strip()]
    vistos = set(partes)
    for texto in novas_entradas:
        if texto not in vistos:
            partes.append(texto)
            vistos.add(texto)
    return '; '.join(partes)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

Tipo = Literal['treinamento', 'ferias', 'atestado']
Origem = Literal['treinamento', 'ferias', 'atestado', 'writer']

_TIPOS_VALIDOS = ('treinamento', 'ferias', 'atestado')
_ORIGENS_VALIDAS = ('treinamento', 'ferias', 'atestado', 'writer')


class _DictLike:
    """
    Mixin: permite acesso dict-like a dataclasses (.get / [key] / in).
    Usado por consumidores que esperavam dicts antes da unificação
    (relatório de inconsistências, GUI, asserts em testes).
    """

    _ALIASES: dict = {}

    def get(self, key, default=None):
        key = self._ALIASES.get(key, key)
        return getattr(self, key, default)

    def __getitem__(self, key):
        key = self._ALIASES.get(key, key)
        if not hasattr(self, key):
            raise KeyError(key)
        return getattr(self, key)

    def __contains__(self, key):
        key = self._ALIASES.get(key, key)
        return hasattr(self, key)


@dataclass
class Update(_DictLike):
    """
    Contrato unificado de atualização produzido por domínios e consumido pelo writer.

    Regras:
      - tipo ∈ {'treinamento','ferias','atestado'} (obrigatório)
      - matricula já normalizada pelo domínio
      - data em 'dd/mm/aaaa'
      - desconto_min em minutos (None se domínio não aplica)
      - situacao permitida quando tipo='ferias' ou tipo='atestado'
      - row=None ⇒ writer expande para todas as linhas do índice (matricula, data)
      - row preenchido ⇒ writer aplica diretamente, sem consultar índice
      - sobrescrever_obs=False ⇒ append com deduplicação (pela observação existente)
      - sobrescrever_obs=True  ⇒ replace da célula
    """
    tipo: Tipo
    matricula: str
    data: str
    observacao: Optional[str] = None
    desconto_min: Optional[int] = None
    situacao: Optional[str] = None
    sobrescrever_obs: bool = False
    row: Optional[int] = None

    # Compat: writer/testes legados acessam 'desconto' em minutos.
    _ALIASES = {'desconto': 'desconto_min'}

    def __post_init__(self):
        if self.tipo not in _TIPOS_VALIDOS:
            raise ValueError(f"Update.tipo inválido: {self.tipo!r}")
        if self.situacao is not None and self.tipo not in ('ferias', 'atestado'):
            raise ValueError(
                f"Update.situacao só é permitida para tipo='ferias' ou tipo='atestado' "
                f"(recebido tipo={self.tipo!r})"
            )


@dataclass
class Inconsistencia(_DictLike):
    """
    Contrato unificado de inconsistência.
    origem é obrigatória (primeiro campo, sem default).
    """
    origem: Origem
    linha: object = '-'
    matricula: str = ''
    data: str = ''
    erro: str = ''

    def __post_init__(self):
        if self.origem not in _ORIGENS_VALIDAS:
            raise ValueError(f"Inconsistencia.origem inválida: {self.origem!r}")


def inconsistencia(origem: Origem, linha='-', matricula='', data='', erro='') -> Inconsistencia:
    """Factory única para inconsistências. origem é argumento posicional obrigatório."""
    return Inconsistencia(
        origem=origem,
        linha=linha,
        matricula=matricula if matricula is not None else '',
        data=data or '',
        erro=erro,
    )
