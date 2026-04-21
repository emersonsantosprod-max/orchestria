"""
pipeline.py — Orquestração do pipeline 3 fases.

Entry point único consumido por CLI e GUI.

Fases:
  1. Leitura (read_only): medição (índice + dados auxiliares) + fontes ativas via loaders.
  2. Processamento em memória (treinamento, ferias, atestado).
  3. Escrita via ZIP patch (excel.aplicar_updates + excel.salvar_via_zip).

Invariantes:
  - Treinamento e férias são opt-in independentes.
  - Updates aplicados na ORDEM: treinamento primeiro, férias depois
    (garante que sobrescrever_obs=True de férias vença quando ambos
    atingirem a mesma célula).
  - Saída vai para o MESMO diretório da Medição selecionada quando
    qualquer caminho custom é fornecido.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field

from app import atestado, db, ferias, loaders, treinamento, excel as writer
from app import validar_distribuicao as vdist
from app.errors import (
    ArquivoAbertoError,
    ArquivoNaoEncontradoError,
    AutomacaoError,
    PlanilhaInvalidaError,
)


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass
class Resultado:
    processados: int = 0
    atualizados: int = 0
    ferias_processadas: int = 0
    ferias_atualizadas: int = 0
    atestados_processados: int = 0
    atestados_atualizados: int = 0
    inconsistencias: list = field(default_factory=list)
    caminho_saida: str = ''


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _mes_referencia(medicao_por_matricula: dict):
    """Deriva mês alvo da menor data do índice da Medição."""
    todas = (
        d for entradas in medicao_por_matricula.values() for d, _, _ in entradas
    )
    menor = min(todas, default=None)
    if menor is None:
        raise RuntimeError("Medição não contém datas válidas para inferir mês de referência.")
    return menor.replace(day=1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def processar(
    caminho_medicao: str,
    caminho_treinamentos: str = '',
    caminho_classificacao: str = '',
    caminho_ferias: str = '',
    caminho_base_cobranca: str = '',
    caminho_atestado: str = '',
    caminho_saida: str = '',
    conn: sqlite3.Connection | None = None,
    validar_distribuicao: bool = False,
) -> Resultado:
    """
    Executa o pipeline completo.

    Flags opt-in:
      - treinamento ativo: ambos caminho_treinamentos e caminho_classificacao
      - férias ativo:      ambos caminho_ferias e caminho_base_cobranca

    Se caminho_saida vazio, usa o diretório da medição.
    """
    if validar_distribuicao and conn is None:
        raise ValueError("validar_distribuicao=True requires conn")

    treinamento_ativo = bool(caminho_treinamentos and caminho_classificacao)
    ferias_ativo      = bool(caminho_ferias and caminho_base_cobranca)
    atestado_ativo    = bool(caminho_atestado)

    if not caminho_saida:
        medicao_dir = os.path.dirname(caminho_medicao) or '.'
        caminho_saida = os.path.join(medicao_dir, 'medicao_processada.xlsx')

    # ------------------------------------------------------------------
    # Fase 1: Leitura
    # ------------------------------------------------------------------
    dados = []
    tabela = {}
    dados_ferias = []
    base_cobranca = {}
    dados_atestado = []

    try:
        if treinamento_ativo:
            dados, tabela = loaders.carregar_dados_treinamento(caminho_treinamentos, caminho_classificacao)
        if ferias_ativo:
            dados_ferias, base_cobranca = loaders.carregar_dados_ferias(caminho_ferias, caminho_base_cobranca)
        if atestado_ativo:
            dados_atestado = loaders.carregar_dados_atestado(caminho_atestado)

        wb_ro, sheet_ro = writer.carregar_planilha(
            caminho_medicao, read_only=True, data_only=True
        )
        col_map = writer.mapear_colunas(sheet_ro)
        (index, obs_existentes, descontos_existentes,
         md_cobranca_por_chave, sg_funcao_por_chave,
         medicao_por_matricula, medicao_records) = writer.indexar_e_ler_dados(sheet_ro, col_map)
        wb_ro.close()

    except FileNotFoundError as e:
        raise ArquivoNaoEncontradoError(str(e)) from e
    except PermissionError as e:
        raise ArquivoAbertoError(str(e)) from e
    except AutomacaoError:
        raise
    except Exception as e:
        raise RuntimeError(f"Erro na fase de leitura: {e}") from e

    # ------------------------------------------------------------------
    # Fase 2: Processamento
    # ------------------------------------------------------------------
    updates_treinamento = []
    inconst_trein = []
    if treinamento_ativo:
        updates_treinamento, inconst_trein = treinamento.processar_treinamentos(
            dados, tabela, obs_existentes
        )

    updates_ferias = []
    inconst_ferias = []
    if ferias_ativo:
        mes_ref = _mes_referencia(medicao_por_matricula)
        updates_ferias, inconst_ferias = ferias.processar_ferias(
            dados_ferias,
            base_cobranca,
            medicao_por_matricula,
            md_cobranca_por_chave,
            sg_funcao_por_chave,
            mes_ref,
            col_map,
        )

    updates_atestado = []
    inconst_atestado = []
    if atestado_ativo:
        updates_atestado, inconst_atestado = atestado.processar_atestados(dados_atestado)

    # ------------------------------------------------------------------
    # Fase 3: Escrita
    # Ordem: treinamento + férias primeiro; atestado em chamada separada.
    # Patches são mesclados com atestado sobrescrevendo (prioridade absoluta).
    # ------------------------------------------------------------------
    try:
        patches_base, inconst_escrita_base = writer.aplicar_updates(
            updates_treinamento + updates_ferias, col_map, index,
            obs_existentes=obs_existentes,
            descontos_existentes=descontos_existentes,
        )
        patches_atestado, inconst_atestado_writer = writer.aplicar_updates(
            updates_atestado, col_map, index,
            obs_existentes=obs_existentes,
            descontos_existentes=descontos_existentes,
        )
        patches = {**patches_base, **patches_atestado}
        inconst_escrita = inconst_escrita_base + inconst_atestado_writer
        writer.salvar_via_zip(caminho_medicao, caminho_saida, patches)
    except PermissionError as e:
        raise ArquivoAbertoError(str(e)) from e
    except AutomacaoError:
        raise
    except Exception as e:
        raise RuntimeError(f"Erro ao gravar arquivo final: {e}") from e

    inconst_validacao = []
    if validar_distribuicao:
        bd_records = db.obter_bd(conn)
        if bd_records:
            inconst_validacao = vdist.validar_para_dominio(bd_records, medicao_records)

    return Resultado(
        processados=len(dados),
        atualizados=len(updates_treinamento),
        ferias_processadas=len(dados_ferias),
        ferias_atualizadas=len(updates_ferias),
        atestados_processados=len(dados_atestado),
        atestados_atualizados=len(updates_atestado) - len(inconst_atestado_writer),
        inconsistencias=inconst_trein + inconst_ferias + inconst_atestado + inconst_escrita + inconst_validacao,
        caminho_saida=caminho_saida,
    )


# ---------------------------------------------------------------------------
# Relatório de inconsistências (.txt)
# ---------------------------------------------------------------------------

def salvar_relatorio_inconsistencias(caminho_dir: str, inconsistencias: list):
    """Gera 'relatorio_inconsistencias.txt' no diretório informado."""
    if not inconsistencias:
        return None

    caminho_saida = os.path.join(caminho_dir, 'relatorio_inconsistencias.txt')
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE INCONSISTÊNCIAS\n")
        f.write("=" * 80 + "\n\n")
        for inc in inconsistencias:
            linha = inc.linha if inc.linha != '' else '-'
            matricula = inc.matricula or '-'
            data = inc.data or '-'
            erro = inc.erro or 'erro desconhecido'
            f.write(f"Linha: {linha} | Matrícula: {matricula} | Data: {data} | Erro: {erro}\n")

    return caminho_saida
