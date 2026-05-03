"""
bootstrap.py — orquestração xlsx → SQLite + leituras de alto nível.

Substitui o antigo `app.infrastructure.db` (deletado). Usa os Repositories
em `app/infrastructure/data/repositories/` para CRUD e adiciona apenas a
camada de orquestração (parse xlsx, transação, registro de arquivo).

Regra: bootstrap.py é o único lugar (junto à composition root) que abre
transação e faz commit. Os Repositories permanecem livres de commit.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import openpyxl

from app.domain.core import normalizar_data
from app.infrastructure.data.registry import RegistryRepository
from app.infrastructure.data.repositories.distribuicao import DistribuicaoRepository
from app.infrastructure.data.repositories.ferias import FeriasRepository
from app.infrastructure.data.repositories.medicao import MedicaoRepository
from app.infrastructure.data.repositories.treinamentos import TreinamentosRepository
from app.infrastructure.paths import bundled_distribuicao_xlsx, bundled_treinamentos_xlsx

logger = logging.getLogger(__name__)

_HEADER_SCAN_ROWS = 20

_ALIASES_MEDICAO = {
    'data':         {'data'},
    'sg_funcao':    {'sg funcao', 'sg função'},
    'md_cobranca':  {'md cobranca', 'md cobrança'},
    'pct_cobranca': {'% cobrança', '% cobranca'},
}


def _normalizar_pct(value) -> float:
    if value is None:
        return 0.0
    v = float(value)
    return v / 100 if v > 1.0 else v


def registrar_bd(path: str | Path, conn: sqlite3.Connection) -> None:
    logger.info('registrar_bd: lendo %s', path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    records: list[tuple] = []
    header_skipped = False
    for row in ws.iter_rows(values_only=True):
        if not header_skipped:
            header_skipped = True
            continue
        if len(row) < 4 or row[0] is None:
            continue
        funcao      = str(row[0]).strip().upper()
        md_cobranca = str(row[1]).strip().upper() if row[1] is not None else ''
        area        = str(row[2]).strip() if row[2] is not None else None
        quantidade  = float(row[3]) if row[3] is not None else 0.0
        records.append((funcao, md_cobranca, area, quantidade))
    wb.close()
    logger.info('registrar_bd: %d linhas extraídas', len(records))

    DistribuicaoRepository(conn).salvar(records)
    RegistryRepository(conn).upsert('bd', str(path))
    conn.commit()


def registrar_medicao(path: str | Path, conn: sqlite3.Connection) -> list[str]:
    """Importa Medição/Frequencia para SQLite. Retorna lista de avisos."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['Frequencia']

    col_map: dict[str, int] | None = None
    records: list[tuple] = []
    tem_maior_1 = False
    tem_menor_igual_1 = False
    linhas_dados_scan = 0

    for row in ws.iter_rows(values_only=True):
        if col_map is None:
            if all(cell is None for cell in row):
                continue
            linhas_dados_scan += 1
            if linhas_dados_scan > _HEADER_SCAN_ROWS:
                break
            candidate: dict[str, int] = {}
            for col_i, cell in enumerate(row):
                if cell is None:
                    continue
                label = str(cell).strip().lower()
                for field, aliases in _ALIASES_MEDICAO.items():
                    if label in aliases and field not in candidate:
                        candidate[field] = col_i
            if len(candidate) == len(_ALIASES_MEDICAO):
                col_map = candidate
            continue

        n = len(row)
        data_val        = row[col_map['data']]         if col_map['data']         < n else None
        sg_funcao_val   = row[col_map['sg_funcao']]    if col_map['sg_funcao']    < n else None
        md_cobranca_val = row[col_map['md_cobranca']]  if col_map['md_cobranca']  < n else None
        pct_val         = row[col_map['pct_cobranca']] if col_map['pct_cobranca'] < n else None

        if data_val is None and sg_funcao_val is None:
            continue

        sg_funcao_str   = str(sg_funcao_val).strip().upper()   if sg_funcao_val   is not None else ''
        md_cobranca_str = str(md_cobranca_val).strip().upper() if md_cobranca_val is not None else ''

        if not sg_funcao_str or not md_cobranca_str:
            continue

        data_str = normalizar_data(data_val)

        if pct_val is not None:
            pv = float(pct_val)
            if pv > 1.0:
                tem_maior_1 = True
            else:
                tem_menor_igual_1 = True

        records.append((data_str, sg_funcao_str, md_cobranca_str, _normalizar_pct(pct_val)))

    wb.close()

    if col_map is None:
        raise ValueError(
            'Cabeçalho da Medição não encontrado nas primeiras '
            f'{_HEADER_SCAN_ROWS} linhas com dados. '
            'Colunas esperadas: data, sg funcao, md cobranca, % cobrança'
        )

    avisos: list[str] = []
    if tem_maior_1 and tem_menor_igual_1:
        avisos.append(
            'AVISO_ESCALA_INDEFINIDA: coluna % Cobrança contém valores em '
            'escalas mistas (alguns > 1.0, alguns ≤ 1.0). '
            'Normalização aplicada linha a linha.'
        )

    MedicaoRepository(conn).salvar(records)
    RegistryRepository(conn).upsert('medicao', str(path))
    conn.commit()
    return avisos


def registrar_base_treinamentos(path: str | Path, conn: sqlite3.Connection) -> None:
    """Importa Base de Treinamentos para `catalogo_treinamentos`."""
    logger.info('registrar_base_treinamentos: lendo %s', path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    records: list[tuple] = []
    for row in wb.active.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        nome = str(row[0]).strip().upper()
        tipo_raw = str(row[1]).strip().lower() if row[1] else ''
        tipo = 'nao_remunerado' if ('não' in tipo_raw or 'nao' in tipo_raw) else 'remunerado'
        records.append((nome, tipo))
    wb.close()
    logger.info('registrar_base_treinamentos: %d treinamentos extraídos', len(records))

    TreinamentosRepository(conn).salvar(records)
    RegistryRepository(conn).upsert('treinamentos', str(path))
    conn.commit()


def registrar_cobranca(path: str | Path, conn: sqlite3.Connection) -> None:
    """Importa base_cobranca.xlsx em `regras_pagamento_ferias`.

    Convenção: `remunerado=0` sse md_cobranca == 'FÉRIAS S/ DESC' (uppercased),
    senão 1 — alinha com o domínio de férias.
    """
    logger.info('registrar_cobranca: lendo %s', path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    records: list[tuple] = []
    for row in wb.active.iter_rows(values_only=True):
        if row[0] is None:
            continue
        sg_funcao = str(row[0]).strip().upper()
        md_cobranca = (
            str(row[1]).strip().upper() if len(row) > 1 and row[1] is not None else ''
        )
        if not sg_funcao:
            continue
        remunerado = 0 if md_cobranca == 'FÉRIAS S/ DESC' else 1
        records.append((sg_funcao, md_cobranca, remunerado))
    wb.close()
    logger.info('registrar_cobranca: %d linhas extraídas', len(records))

    FeriasRepository(conn).salvar(records)
    RegistryRepository(conn).upsert('cobranca', str(path))
    conn.commit()


def obter_bd(conn: sqlite3.Connection) -> list[dict]:
    return DistribuicaoRepository(conn).listar()


def obter_medicao(conn: sqlite3.Connection) -> list[dict]:
    return MedicaoRepository(conn).listar()


def obter_cobranca(conn: sqlite3.Connection) -> dict[str, str]:
    return FeriasRepository(conn).obter_mapa()


def obter_tabela_treinamento(conn: sqlite3.Connection) -> dict[str, str]:
    return TreinamentosRepository(conn).obter()


def obter_registro_arquivos(conn: sqlite3.Connection) -> dict[str, dict]:
    return RegistryRepository(conn).get_all()


def popular_bd_se_vazio(conn: sqlite3.Connection) -> bool:
    """Bootstrap idempotente de bd_distribuicao a partir do xlsx empacotado."""
    if DistribuicaoRepository(conn).count() > 0:
        return False
    if RegistryRepository(conn).get('bd') is not None:
        return False
    xlsx = bundled_distribuicao_xlsx()
    if not xlsx.exists():
        logger.info('popular_bd_se_vazio: xlsx empacotado ausente em %s', xlsx)
        return False
    try:
        registrar_bd(xlsx, conn)
    except Exception:
        conn.rollback()
        logger.exception('popular_bd_se_vazio: rollback após falha')
        raise
    return True


def popular_treinamentos_se_vazio(conn: sqlite3.Connection) -> bool:
    """Bootstrap idempotente de catalogo_treinamentos a partir do xlsx empacotado."""
    if TreinamentosRepository(conn).count() > 0:
        return False
    if RegistryRepository(conn).get('treinamentos') is not None:
        return False
    xlsx = bundled_treinamentos_xlsx()
    if not xlsx.exists():
        logger.info('popular_treinamentos_se_vazio: xlsx empacotado ausente em %s', xlsx)
        return False
    try:
        registrar_base_treinamentos(xlsx, conn)
    except Exception:
        conn.rollback()
        logger.exception('popular_treinamentos_se_vazio: rollback após falha')
        raise
    return True


def popular_cobranca_se_vazio(conn: sqlite3.Connection, xlsx: Path | str | None = None) -> bool:
    """Bootstrap idempotente de regras_pagamento_ferias a partir de xlsx informado."""
    if FeriasRepository(conn).count() > 0:
        return False
    if RegistryRepository(conn).get('cobranca') is not None:
        return False
    if xlsx is None or not Path(xlsx).exists():
        return False
    try:
        registrar_cobranca(xlsx, conn)
    except Exception:
        conn.rollback()
        logger.exception('popular_cobranca_se_vazio: rollback após falha')
        raise
    return True
