import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, scrolledtext

try:
    import openpyxl  # noqa: F401  (fail-soft: alguns builds empacotam lazy)
except ImportError:
    pass


def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")


base_path = get_base_path()
app_path = os.path.join(base_path, "app")
if app_path not in sys.path:
    sys.path.append(app_path)

from app.pipeline import processar, salvar_relatorio_inconsistencias
from app import db
from app.validar_distribuicao import validar, gerar_relatorio, _salvar_relatorio


# ---------------------------------------------------------------------------
# Seleção de arquivos
# ---------------------------------------------------------------------------

def selecionar_arquivo(titulo):
    return filedialog.askopenfilename(
        title=titulo,
        filetypes=[("Arquivos Excel", "*.xlsx")],
    )


# ---------------------------------------------------------------------------
# Handlers genéricos de fluxo (treinamento e férias compartilham estrutura)
# ---------------------------------------------------------------------------

def _desabilitar_botoes():
    botao_lancar.config(state=tk.DISABLED)
    botao_ferias.config(state=tk.DISABLED)
    botao_atestado.config(state=tk.DISABLED)
    botao_validar.config(state=tk.DISABLED)


def _habilitar_botoes():
    janela.after(0, lambda: botao_lancar.config(state=tk.NORMAL))
    janela.after(0, lambda: botao_ferias.config(state=tk.NORMAL))
    janela.after(0, lambda: botao_atestado.config(state=tk.NORMAL))
    janela.after(0, lambda: botao_validar.config(state=tk.NORMAL))


def _executar_fluxo(titulo_log: str, prompts: list, montar_kwargs):
    """
    Fluxo genérico: limpa log, pede arquivos via prompts, executa service.processar.

    prompts:  lista de (label, chave_kwargs). Primeiro é sempre a medição.
    montar_kwargs: função (caminhos_dict) -> kwargs para service.processar.
    """
    _desabilitar_botoes()
    area_saida.delete(1.0, tk.END)

    caminhos = {}
    for label, chave in prompts:
        caminho = selecionar_arquivo(label)
        if not caminho:
            imprimir_log(f"Operação cancelada: {label} não foi selecionada.\n")
            _habilitar_botoes()
            return
        caminhos[chave] = caminho

    imprimir_log(f"Iniciando {titulo_log}...\n")

    def tarefa():
        conn = db.conectar()
        try:
            db.popular_bd_se_vazio(conn)
            imprimir_log("Fase 1/3: Lendo arquivos (modo otimizado)...\n")
            resultado = processar(
                **montar_kwargs(caminhos),
                conn=conn,
                validar_distribuicao=True,
            )
            imprimir_log("Fase 2/3: Processando regras de negócio...\n")
            imprimir_log("Fase 3/3: Gravando resultados no Excel (isso pode demorar)...\n")
            mostrar_resultado(resultado)
        except Exception as e:
            imprimir_log(f"\n[ERRO] {str(e)}")
        finally:
            conn.close()
            _habilitar_botoes()

    threading.Thread(target=tarefa, daemon=True).start()


def iniciar_lancamento():
    _executar_fluxo(
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


def iniciar_ferias():
    _executar_fluxo(
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


def iniciar_atestado():
    _executar_fluxo(
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


def iniciar_validacao():
    _desabilitar_botoes()
    area_saida.delete(1.0, tk.END)

    conn = db.conectar()
    db.popular_bd_se_vazio(conn)
    registros = db.obter_registro_arquivos(conn)
    conn.close()

    caminho_bd = None
    caminho_medicao = None

    if 'medicao' not in registros:
        imprimir_log("Medição não registrada — solicitando arquivo...\n")
        caminho_medicao = selecionar_arquivo("Selecione o arquivo de Medição Frequência")
        if not caminho_medicao:
            imprimir_log("Operação cancelada: Medição não foi selecionada.\n")
            _habilitar_botoes()
            return

    imprimir_log("Executando validação...\n")

    def tarefa():
        try:
            conn = db.conectar()
            avisos_import = []

            if caminho_bd:
                imprimir_log("Registrando BD...\n")
                db.registrar_bd(caminho_bd, conn)

            if caminho_medicao:
                imprimir_log("Registrando Medição...\n")
                avisos = db.registrar_medicao(caminho_medicao, conn)
                avisos_import.extend(avisos)

            registros_atuais = db.obter_registro_arquivos(conn)
            bd_records       = db.obter_bd(conn)
            medicao_records  = db.obter_medicao(conn)
            conn.close()

            inconsistencias = validar(bd_records, medicao_records)

            bd_pares = {(r['funcao'], r['md_cobranca']) for r in bd_records}
            datas    = {r['data'] for r in medicao_records}

            conteudo    = gerar_relatorio(
                inconsistencias, registros_atuais,
                n_pares_bd=len(bd_pares),
                n_datas=len(datas),
                avisos_import=avisos_import,
            )
            caminho_rel = _salvar_relatorio(conteudo)

            imprimir_log(f"Relatório gerado em: {caminho_rel}\n")
            imprimir_log(f"Total de inconsistências: {len(inconsistencias)}\n")
            for av in avisos_import:
                imprimir_log(f"[AVISO] {av}\n")

        except Exception as e:
            imprimir_log(f"\n[ERRO] {str(e)}\n")
        finally:
            _habilitar_botoes()

    threading.Thread(target=tarefa, daemon=True).start()


# ---------------------------------------------------------------------------
# Saída / relatório
# ---------------------------------------------------------------------------

def mostrar_resultado(resultado):
    """Formata o Resultado do service e exibe no log; exporta .txt se houver inconsistências."""
    processados = resultado.processados
    atualizados = resultado.atualizados
    ferias_proc = resultado.ferias_processadas
    ferias_atu  = resultado.ferias_atualizadas
    atestados_proc = resultado.atestados_processados
    atestados_atu  = resultado.atestados_atualizados
    inconsistencias = resultado.inconsistencias
    caminho_saida = resultado.caminho_saida

    log = (
        "Processamento Concluído com Sucesso!\n"
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
            mat = inc.matricula or '-'
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

    imprimir_log(log)


def imprimir_log(texto):
    def inserir():
        area_saida.insert(tk.END, texto)
        area_saida.see(tk.END)
    janela.after(0, inserir)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

janela = tk.Tk()
janela.title("Automação de Medição")
janela.geometry("600x500")
janela.update_idletasks()
_w = janela.winfo_width()
_h = janela.winfo_height()
_x = (janela.winfo_screenwidth() - _w) // 2
_y = (janela.winfo_screenheight() - _h) // 2
janela.geometry(f"{_w}x{_h}+{_x}+{_y}")
janela.configure(padx=20, pady=20)

lbl_titulo = tk.Label(
    janela,
    text="Automação de Medição",
    font=("Arial", 16, "bold"),
)
lbl_titulo.pack(pady=(0, 20))

frame_botoes = tk.Frame(janela)
frame_botoes.pack(fill=tk.X, pady=(0, 20))

botao_lancar = tk.Button(
    frame_botoes,
    text="Lançar treinamentos",
    command=iniciar_lancamento,
    font=("Arial", 11),
    height=2,
    width=20,
)
botao_lancar.pack(side=tk.LEFT, padx=5)

botao_ferias = tk.Button(
    frame_botoes,
    text="Lançar Férias",
    command=iniciar_ferias,
    font=("Arial", 11),
    height=2,
    width=20,
)
botao_ferias.pack(side=tk.LEFT, padx=5)

botao_atestado = tk.Button(
    frame_botoes,
    text="Lançar Atestados",
    command=iniciar_atestado,
    font=("Arial", 11),
    height=2,
    width=20,
)
botao_atestado.pack(side=tk.LEFT, padx=5)

botao_validar = tk.Button(
    frame_botoes,
    text="Validar Distribuição",
    command=iniciar_validacao,
    font=("Arial", 11),
    height=2,
    width=20,
)
botao_validar.pack(side=tk.LEFT, padx=5)

lbl_saida = tk.Label(janela, text="Log de Execução:", font=("Arial", 10))
lbl_saida.pack(anchor=tk.W, pady=(10, 5))

area_saida = scrolledtext.ScrolledText(
    janela,
    width=70,
    height=15,
    font=("Courier", 10),
    bg="#f4f4f4",
)
area_saida.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    try:
        janela.mainloop()
    except Exception as e:
        caminho_fatal = os.path.join(str(Path.home()), "Downloads", "erro_fatal_automacao.txt")
        with open(caminho_fatal, "w", encoding="utf-8") as f:
            import traceback
            f.write(f"ERRO FATAL QUE FECHOU A TELA:\n\n{str(e)}\n\n")
            f.write(traceback.format_exc())
        sys.exit(1)
