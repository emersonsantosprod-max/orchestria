"""Handlers da GUI: fluxos assíncronos de treinamento/férias/atestado/validação."""

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog

from app import db
from app.errors import (
    ArquivoAbertoError,
    ArquivoNaoEncontradoError,
    AutomacaoError,
    ConversaoArquivoError,
    PlanilhaInvalidaError,
)
from app.loaders import carregar_medicao_hr
from app.pipeline import executar_pipeline, salvar_relatorio_inconsistencias
from app.validar_distribuicao import _salvar_relatorio, gerar_relatorio, validar_aderencia_distribuicao
from app.validar_horas import (
    _salvar_relatorio as _salvar_relatorio_hr,
)
from app.validar_horas import (
    gerar_relatorio as _gerar_relatorio_hr,
)
from app.validar_horas import (
    validar_horas_trabalhadas as _validar_hr,
)


@dataclass
class GuiContext:
    imprimir_log: Callable[[str], None]
    limpar_log: Callable[[], None]
    desabilitar_botoes: Callable[[], None]
    habilitar_botoes: Callable[[], None]


def mensagem_erro(exc: BaseException) -> str:
    if isinstance(exc, ArquivoAbertoError):
        return (
            "Não foi possível acessar o arquivo. Verifique se ele está "
            "aberto no Excel e feche antes de tentar novamente."
        )
    if isinstance(exc, ArquivoNaoEncontradoError):
        return f"Arquivo não encontrado: {exc}"
    if isinstance(exc, PlanilhaInvalidaError):
        return f"Planilha inválida: {exc}"
    if isinstance(exc, ConversaoArquivoError):
        return f"Falha ao converter arquivo: {exc}"
    if isinstance(exc, AutomacaoError):
        return str(exc)
    return f"Erro inesperado: {exc}"


def selecionar_arquivo(titulo: str) -> str:
    return filedialog.askopenfilename(
        title=titulo,
        filetypes=[("Arquivos Excel", "*.xlsx")],
    )


def _executar_fluxo(ctx: GuiContext, titulo_log: str, prompts, montar_kwargs):
    ctx.desabilitar_botoes()
    ctx.limpar_log()

    caminhos = {}
    for label, chave in prompts:
        caminho = selecionar_arquivo(label)
        if not caminho:
            ctx.imprimir_log(f"Operação cancelada: {label} não foi selecionada.\n")
            ctx.habilitar_botoes()
            return
        caminhos[chave] = caminho

    ctx.imprimir_log(f"Iniciando {titulo_log}...\n")

    def tarefa():
        conn = db.conectar()
        try:
            db.popular_bd_se_vazio(conn)
            ctx.imprimir_log("Fase 1/3: Lendo arquivos (modo otimizado)...\n")
            resultado = executar_pipeline(
                **montar_kwargs(caminhos),
                conn=conn,
                validar_distribuicao=False,
            )
            ctx.imprimir_log("Fase 2/3: Processando regras de negócio...\n")
            ctx.imprimir_log("Fase 3/3: Gravando resultados no Excel (isso pode demorar)...\n")
            mostrar_resultado(ctx, resultado)
        except Exception as e:
            ctx.imprimir_log(f"\n[ERRO] {mensagem_erro(e)}\n")
        finally:
            conn.close()
            ctx.habilitar_botoes()

    threading.Thread(target=tarefa, daemon=True).start()


def iniciar_lancamento(ctx: GuiContext):
    _executar_fluxo(
        ctx,
        titulo_log="processamento de treinamentos",
        prompts=[
            ("1. Selecione a planilha de Medição Destino", 'medicao'),
            ("2. Selecione a planilha de Treinamentos Realizados", 'treinamentos'),
            ("3. Selecione a Base de Treinamentos (Classificação)", 'classificacao'),
        ],
        montar_kwargs=lambda c: dict(
            caminho_medicao=c['medicao'],
            caminho_treinamentos=c['treinamentos'],
            caminho_classificacao=c['classificacao'],
        ),
    )


def iniciar_ferias(ctx: GuiContext):
    _executar_fluxo(
        ctx,
        titulo_log="processamento de férias",
        prompts=[
            ("1. Selecione a planilha de Medição Destino", 'medicao'),
            ("2. Selecione o Relatório Geral de Férias", 'ferias'),
            ("3. Selecione a Base de Cobrança (SgFunção → Categoria)", 'base_cobranca'),
        ],
        montar_kwargs=lambda c: dict(
            caminho_medicao=c['medicao'],
            caminho_ferias=c['ferias'],
            caminho_base_cobranca=c['base_cobranca'],
        ),
    )


def iniciar_atestado(ctx: GuiContext):
    _executar_fluxo(
        ctx,
        titulo_log="processamento de atestados médicos",
        prompts=[
            ("1. Selecione a planilha de Medição Destino", 'medicao'),
            ("2. Selecione o arquivo de Atestados Médicos", 'atestado'),
        ],
        montar_kwargs=lambda c: dict(
            caminho_medicao=c['medicao'],
            caminho_atestado=c['atestado'],
        ),
    )


def iniciar_validacao(ctx: GuiContext):
    ctx.desabilitar_botoes()
    ctx.limpar_log()

    try:
        conn = db.conectar()
        db.popular_bd_se_vazio(conn)
        registros = db.obter_registro_arquivos(conn)
        conn.close()
    except Exception as e:
        ctx.imprimir_log(f"\n[ERRO] {mensagem_erro(e)}\n")
        ctx.habilitar_botoes()
        return

    caminho_bd = None
    caminho_medicao = None

    if 'bd' not in registros:
        ctx.imprimir_log("BD não registrado — solicitando arquivo...\n")
        caminho_bd = selecionar_arquivo("Selecione o arquivo de BD de Distribuição Contratual")
        if not caminho_bd:
            ctx.imprimir_log("Operação cancelada: BD não foi selecionado.\n")
            ctx.habilitar_botoes()
            return

    if 'medicao' not in registros:
        ctx.imprimir_log("Medição não registrada — solicitando arquivo...\n")
        caminho_medicao = selecionar_arquivo("Selecione o arquivo de Medição Frequência")
        if not caminho_medicao:
            ctx.imprimir_log("Operação cancelada: Medição não foi selecionada.\n")
            ctx.habilitar_botoes()
            return

    ctx.imprimir_log("Executando validação...\n")

    def tarefa():
        try:
            conn = db.conectar()
            avisos_import = []

            if caminho_bd:
                ctx.imprimir_log("Registrando BD...\n")
                db.registrar_bd(caminho_bd, conn)

            if caminho_medicao:
                ctx.imprimir_log("Registrando Medição...\n")
                avisos = db.registrar_medicao(caminho_medicao, conn)
                avisos_import.extend(avisos)

            registros_atuais = db.obter_registro_arquivos(conn)
            bd_records       = db.obter_bd(conn)
            medicao_records  = db.obter_medicao(conn)
            conn.close()

            inconsistencias = validar_aderencia_distribuicao(bd_records, medicao_records)

            bd_pares = {(r['funcao'], r['md_cobranca']) for r in bd_records}
            datas    = {r['data'] for r in medicao_records}

            conteudo = gerar_relatorio(
                inconsistencias, registros_atuais,
                n_pares_bd=len(bd_pares),
                n_datas=len(datas),
                avisos_import=avisos_import,
            )
            caminho_rel = _salvar_relatorio(conteudo)

            ctx.imprimir_log(f"Relatório gerado em: {caminho_rel}\n")
            ctx.imprimir_log(f"Total de inconsistências: {len(inconsistencias)}\n")
            for av in avisos_import:
                ctx.imprimir_log(f"[AVISO] {av}\n")

        except Exception as e:
            ctx.imprimir_log(f"\n[ERRO] {mensagem_erro(e)}\n")
        finally:
            ctx.habilitar_botoes()

    threading.Thread(target=tarefa, daemon=True).start()


def iniciar_validar_hr(ctx: GuiContext):
    ctx.desabilitar_botoes()
    ctx.limpar_log()

    caminho = selecionar_arquivo("Selecione a planilha de Medição")
    if not caminho:
        ctx.imprimir_log("Operação cancelada: arquivo não foi selecionado.\n")
        ctx.habilitar_botoes()
        return

    ctx.imprimir_log("Validando horas trabalhadas...\n")

    def tarefa():
        try:
            registros, n_linhas = carregar_medicao_hr(caminho)
            inconsistencias = _validar_hr(registros)
            conteudo = _gerar_relatorio_hr(inconsistencias, str(Path(caminho).resolve()), n_linhas)
            caminho_rel = _salvar_relatorio_hr(conteudo)
            ctx.imprimir_log(f"Relatório gerado em: {caminho_rel}\n")
            ctx.imprimir_log(f"Total de inconsistências: {len(inconsistencias)}\n")
        except Exception as e:
            ctx.imprimir_log(f"\n[ERRO] {mensagem_erro(e)}\n")
        finally:
            ctx.habilitar_botoes()

    threading.Thread(target=tarefa, daemon=True).start()


def mostrar_resultado(ctx: GuiContext, resultado):
    processados    = resultado.processados
    atualizados    = resultado.atualizados
    ferias_proc    = resultado.ferias_processadas
    ferias_atu     = resultado.ferias_atualizadas
    atestados_proc = resultado.atestados_processados
    atestados_atu  = resultado.atestados_atualizados
    inconsistencias = resultado.inconsistencias
    caminho_saida   = resultado.caminho_saida

    log = (
        "Processamento concluído com sucesso.\n"
        "--------------------------------------------------\n"
        f"Treinamentos processados: {processados}\n"
        f"Treinamentos atualizados: {atualizados}\n"
        f"Férias processadas:       {ferias_proc}\n"
        f"Linhas com férias:        {ferias_atu}\n"
        f"Atestados processados:    {atestados_proc}\n"
        f"Linhas com atestado:      {atestados_atu}\n"
    )
    nome_arquivo = os.path.basename(caminho_saida)
    log += f"Arquivo gerado:         {nome_arquivo}\n"
    log += f"Inconsistências totais: {len(inconsistencias)}\n"

    if inconsistencias:
        log += "\n--- LISTA DE INCONSISTÊNCIAS (preview: primeiros 10) ---\n"
        for inc in inconsistencias[:10]:
            mat  = inc.matricula or '-'
            data = inc.data or '-'
            erro = inc.erro or 'erro desconhecido'
            log += f"{mat} | {data} | {erro}\n"
        if len(inconsistencias) > 10:
            log += f"... ({len(inconsistencias) - 10} inconsistências adicionais no relatório)\n"

        selected_dir = filedialog.askdirectory(
            title="Selecione o diretório para salvar o relatório de inconsistências"
        )
        output_dir = selected_dir if selected_dir else os.path.dirname(caminho_saida)
        log += "\nExportando relatório de inconsistências...\n"
        caminho_relatorio = salvar_relatorio_inconsistencias(output_dir, inconsistencias)
        if caminho_relatorio:
            log += f"Relatório salvo: {caminho_relatorio}\n"

    ctx.imprimir_log(log)
