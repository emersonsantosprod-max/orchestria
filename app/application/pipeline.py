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

import logging
import os
import sqlite3
from dataclasses import dataclass, field

from app.application.services import validacao_distribuicao as vdist
from app.application.services.lancar_treinamentos import LancarTreinamentosService
from app.domain import atestado, ferias
from app.domain.core import inconsistencia
from app.domain.errors import (
    ArquivoAbertoError,
    ArquivoNaoEncontradoError,
    AutomacaoError,
    PlanilhaInvalidaError,
)
from app.infrastructure import db, loaders
from app.infrastructure import excel as writer
from app.infrastructure.adapters.sqlite_tabela_classificacao import SqliteTabelaClassificacao

logger = logging.getLogger(__name__)


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


def _mes_referencia(medicao_por_matricula: dict):
    """Deriva mês alvo da menor data do índice da Medição.

    Levanta PlanilhaInvalidaError se as datas atravessarem mais de um mês —
    férias derivam a janela de aplicação a partir desse mês inferido, e datas
    em meses distintos silenciariam metade do período de férias.
    """
    todas = [
        d for entradas in medicao_por_matricula.values() for d, _, _ in entradas
    ]
    if not todas:
        raise RuntimeError("Medição não contém datas válidas para inferir mês de referência.")
    meses = {(d.year, d.month) for d in todas}
    if len(meses) > 1:
        rotulos = sorted(f"{ano:04d}-{mes:02d}" for ano, mes in meses)
        raise PlanilhaInvalidaError(
            "Medição contém datas em múltiplos meses: " + ", ".join(rotulos)
        )
    return min(todas).replace(day=1)


def derivar_mes_referencia_da_medicao(caminho_medicao: str):
    """Lê a Medição e retorna o mês de referência (date, primeiro dia do mês).

    Boundary pública para consumo externo (HTTP `POST /api/session/medicao`,
    GUI, qualquer entry-point que precise validar a Medição antes do pipeline).
    Usa o mesmo `_mes_referencia` interno para garantir SSOT — qualquer outra
    derivação (header cell, filename) divergiria do valor que `executar_pipeline`
    aceita e geraria PlanilhaInvalidaError no momento errado.
    """
    try:
        wb_ro, sheet_ro = writer.carregar_planilha(
            caminho_medicao, read_only=True, data_only=True
        )
        try:
            col_map = writer.mapear_colunas(sheet_ro)
            (_index, _obs, _desc, _md, _sg,
             medicao_por_matricula, _records,
             _obs_div, _desc_div) = writer.indexar_e_ler_dados(sheet_ro, col_map)
        finally:
            wb_ro.close()
    except FileNotFoundError as e:
        raise ArquivoNaoEncontradoError(str(e)) from e
    except PermissionError as e:
        raise ArquivoAbertoError(str(e)) from e
    return _mes_referencia(medicao_por_matricula)


def executar_pipeline(
    caminho_medicao: str,
    caminho_treinamentos: str = '',
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
      - treinamento ativo: caminho_treinamentos fornecido E conn não é None
      - férias ativo:      ambos caminho_ferias e caminho_base_cobranca

    Se caminho_saida vazio, usa o diretório da medição.
    """
    if validar_distribuicao and conn is None:
        raise ValueError("validar_distribuicao=True requires conn")

    treinamento_ativo = bool(caminho_treinamentos and conn is not None)
    ferias_ativo      = bool(caminho_ferias and caminho_base_cobranca)
    atestado_ativo    = bool(caminho_atestado)
    logger.info(
        'executar_pipeline: treinamento=%s ferias=%s atestado=%s validar_dist=%s',
        treinamento_ativo, ferias_ativo, atestado_ativo, validar_distribuicao,
    )

    if not caminho_saida:
        medicao_dir = os.path.dirname(caminho_medicao) or '.'
        caminho_saida = os.path.join(medicao_dir, 'medicao_processada.xlsx')

    dados = []
    dados_ferias = []
    base_cobranca = {}
    dados_atestado = []

    servico_treinamentos: LancarTreinamentosService | None = None
    if treinamento_ativo:
        tabela_classif = SqliteTabelaClassificacao(conn)
        if not tabela_classif.obter():
            raise ValueError(
                "bd_treinamentos está vazio. Verifique se assets/base_treinamentos.xlsx "
                "está empacotado e se o bootstrap foi chamado na application boundary."
            )
        servico_treinamentos = LancarTreinamentosService(tabela_classif)

    logger.info('executar_pipeline: fase 1 (leitura) iniciando')
    try:
        if treinamento_ativo:
            dados = loaders.carregar_dados_treinamento(caminho_treinamentos)
        if ferias_ativo:
            dados_ferias, base_cobranca = loaders.carregar_dados_ferias(caminho_ferias, caminho_base_cobranca)
        if atestado_ativo:
            dados_atestado = loaders.carregar_dados_atestado(caminho_atestado)

        logger.info('executar_pipeline: lendo medição %s', caminho_medicao)
        wb_ro, sheet_ro = writer.carregar_planilha(
            caminho_medicao, read_only=True, data_only=True
        )
        col_map = writer.mapear_colunas(sheet_ro)
        faltantes_validacao = [
            k for k in ('sg_funcao', 'md_cobranca', 'pct_cobranca')
            if k in col_map.get('_ausentes', ())
        ]
        (index, obs_existentes, descontos_existentes,
         md_cobranca_por_chave, sg_funcao_por_chave,
         medicao_por_matricula, medicao_records,
         obs_divergentes, desc_divergentes) = writer.indexar_e_ler_dados(sheet_ro, col_map)
        wb_ro.close()
        logger.info('executar_pipeline: fase 1 concluída (%d chaves indexadas)', len(index))

    except FileNotFoundError as e:
        raise ArquivoNaoEncontradoError(str(e)) from e
    except PermissionError as e:
        raise ArquivoAbertoError(str(e)) from e
    except AutomacaoError:
        raise
    except Exception as e:
        raise RuntimeError(f"Erro na fase de leitura: {e}") from e

    logger.info('executar_pipeline: fase 2 (domínio) iniciando')
    updates_treinamento = []
    inconst_trein = []
    if treinamento_ativo:
        logger.info('executar_pipeline: domínio treinamento')
        assert servico_treinamentos is not None
        updates_treinamento, inconst_trein = servico_treinamentos.executar(
            dados, obs_existentes
        )

    updates_ferias = []
    inconst_ferias = []
    if ferias_ativo:
        logger.info('executar_pipeline: domínio férias')
        mes_ref = _mes_referencia(medicao_por_matricula)
        updates_ferias, inconst_ferias = ferias.gerar_updates_ferias(
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
        logger.info('executar_pipeline: domínio atestado')
        updates_atestado, inconst_atestado = atestado.gerar_updates_atestado(dados_atestado)
    logger.info('executar_pipeline: fase 2 concluída')

    # Ordem: treinamento + férias primeiro; atestado em chamada separada.
    # Patches são mesclados com atestado sobrescrevendo (prioridade absoluta).
    logger.info('executar_pipeline: fase 3 (escrita) iniciando')
    try:
        patches_base, inconst_escrita_base = writer.aplicar_updates(
            updates_treinamento + updates_ferias, col_map, index,
            obs_existentes=obs_existentes,
            descontos_existentes=descontos_existentes,
            obs_divergentes=obs_divergentes,
            desc_divergentes=desc_divergentes,
        )
        patches_atestado, inconst_atestado_writer = writer.aplicar_updates(
            updates_atestado, col_map, index,
            obs_existentes=obs_existentes,
            descontos_existentes=descontos_existentes,
            obs_divergentes=obs_divergentes,
            desc_divergentes=desc_divergentes,
        )
        patches = {**patches_base, **patches_atestado}
        inconst_escrita = inconst_escrita_base + inconst_atestado_writer
        logger.info('executar_pipeline: salvar_via_zip → %s', caminho_saida)
        writer.salvar_via_zip(caminho_medicao, caminho_saida, patches)
        logger.info('executar_pipeline: fase 3 concluída')
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
            if faltantes_validacao:
                inconst_validacao = [inconsistencia(
                    origem='writer',
                    erro=(
                        "validar_distribuicao=True ignorado: medição sem colunas "
                        + ", ".join(faltantes_validacao)
                    ),
                )]
            else:
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
