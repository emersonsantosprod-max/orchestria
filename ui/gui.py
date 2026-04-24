import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

import customtkinter as ctk


def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")


base_path = get_base_path()
app_path = os.path.join(base_path, "app")
if app_path not in sys.path:
    sys.path.append(app_path)

from ui.gui_handlers import (
    GuiContext,
    iniciar_atestado,
    iniciar_ferias,
    iniciar_importar_base_treinamentos,
    iniciar_lancamento,
    iniciar_validacao,
    iniciar_validar_hr,
)

_CHUMBO      = "#232323"
_CHUMBO_2    = "#111111"
_LARANJA     = "#ff460a"
_LARANJA_HV  = "#e2360e"
_CONTEUDO    = "#ededed"
_PAINEL      = "#ffffff"
_TXT_INV     = "#ffffff"
_TXT_NAV     = "#e5e5e5"


def _todos_botoes():
    return [botao_lancar, botao_ferias, botao_atestado, botao_importar_base, botao_validar, botao_validar_hr]


def _desabilitar_botoes():
    for b in _todos_botoes():
        b.configure(state="disabled")


def _habilitar_botoes():
    janela.after(0, lambda: [b.configure(state="normal") for b in _todos_botoes()])


def imprimir_log(texto):
    def inserir():
        area_saida.insert("end", texto)
        area_saida.see("end")
    janela.after(0, inserir)


def _limpar_log():
    area_saida.delete("1.0", "end")


def _ativar_aba(tab_id):
    if tab_id == 'lancar':
        nav_lancar.configure(fg_color=_LARANJA, text_color=_TXT_INV, font=_fonte_nav_ativo)
        nav_validacao.configure(fg_color="transparent", text_color=_TXT_NAV, font=_fonte_nav)
        frame_validacao.pack_forget()
        frame_lancar.pack(padx=16, pady=12, fill="x")
    else:
        nav_lancar.configure(fg_color="transparent", text_color=_TXT_NAV, font=_fonte_nav)
        nav_validacao.configure(fg_color=_LARANJA, text_color=_TXT_INV, font=_fonte_nav_ativo)
        frame_lancar.pack_forget()
        frame_validacao.pack(padx=16, pady=12, fill="x")


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

janela = ctk.CTk()
janela.title("Automação de Medição")
janela.geometry("1080x580")
janela.minsize(960, 500)

_familia = "IBM Plex Sans" if "IBM Plex Sans" in tkfont.families() else "Segoe UI"
_w, _h = 1080, 580
_x = (janela.winfo_screenwidth() - _w) // 2
_y = (janela.winfo_screenheight() - _h) // 2
janela.geometry(f"{_w}x{_h}+{_x}+{_y}")

_fonte_nav      = ctk.CTkFont(family=_familia, size=13)
_fonte_nav_ativo = ctk.CTkFont(family=_familia, size=13, weight="bold")
_fonte_heading  = ctk.CTkFont(family=_familia, size=14, weight="bold")
_fonte_botao    = ctk.CTkFont(family=_familia, size=12)
_fonte_label    = ctk.CTkFont(family=_familia, size=11)
_fonte_log      = ctk.CTkFont(family="Courier New", size=10)

janela.grid_columnconfigure(1, weight=1)
janela.grid_rowconfigure(0, weight=1)

sidebar = ctk.CTkFrame(janela, width=200, corner_radius=0, fg_color=_CHUMBO)
sidebar.grid(row=0, column=0, sticky="nsew")
sidebar.grid_propagate(False)
sidebar.grid_columnconfigure(0, weight=1)
sidebar.grid_rowconfigure(5, weight=1)

ctk.CTkLabel(
    sidebar,
    text="Automação de\nMedição",
    font=_fonte_heading,
    text_color=_TXT_INV,
    justify="left",
    anchor="w",
).grid(row=0, column=0, padx=18, pady=(20, 6), sticky="w")

tk.Frame(sidebar, height=1, bg="#3a3a3a").grid(
    row=1, column=0, padx=18, pady=(2, 10), sticky="ew"
)

ctk.CTkLabel(
    sidebar,
    text="MÓDULOS",
    font=ctk.CTkFont(family=_familia, size=10, weight="bold"),
    text_color="#6a6a6a",
    anchor="w",
).grid(row=2, column=0, padx=18, pady=(0, 4), sticky="w")

nav_lancar = ctk.CTkButton(
    sidebar,
    text="Lançar",
    font=_fonte_nav_ativo,
    fg_color=_LARANJA,
    hover_color=_LARANJA_HV,
    text_color=_TXT_INV,
    anchor="w",
    corner_radius=4,
    height=36,
    command=lambda: _ativar_aba('lancar'),
)
nav_lancar.grid(row=3, column=0, padx=8, pady=2, sticky="ew")

nav_validacao = ctk.CTkButton(
    sidebar,
    text="Validação",
    font=_fonte_nav,
    fg_color="transparent",
    hover_color=_CHUMBO_2,
    text_color=_TXT_NAV,
    anchor="w",
    corner_radius=4,
    height=36,
    command=lambda: _ativar_aba('validacao'),
)
nav_validacao.grid(row=4, column=0, padx=8, pady=2, sticky="ew")

ctk.CTkLabel(
    sidebar,
    text="Manserv · 2026",
    font=ctk.CTkFont(family=_familia, size=10),
    text_color="#555555",
    anchor="w",
).grid(row=6, column=0, padx=18, pady=(0, 12), sticky="sw")

content = ctk.CTkFrame(janela, corner_radius=0, fg_color=_CONTEUDO)
content.grid(row=0, column=1, sticky="nsew")

painel_botoes = ctk.CTkFrame(content, corner_radius=0, fg_color=_PAINEL)
painel_botoes.pack(fill="x")

_ctx = GuiContext(
    imprimir_log=imprimir_log,
    limpar_log=_limpar_log,
    desabilitar_botoes=_desabilitar_botoes,
    habilitar_botoes=_habilitar_botoes,
)

frame_lancar = ctk.CTkFrame(painel_botoes, fg_color=_PAINEL, corner_radius=0)

botao_lancar = ctk.CTkButton(
    frame_lancar,
    text="Lançar treinamentos",
    font=_fonte_botao,
    fg_color=_LARANJA,
    hover_color=_LARANJA_HV,
    text_color=_TXT_INV,
    corner_radius=4,
    height=36,
    command=lambda: iniciar_lancamento(_ctx),
)
botao_lancar.pack(side="left", padx=(0, 8))

botao_ferias = ctk.CTkButton(
    frame_lancar,
    text="Lançar férias",
    font=_fonte_botao,
    fg_color=_LARANJA,
    hover_color=_LARANJA_HV,
    text_color=_TXT_INV,
    corner_radius=4,
    height=36,
    command=lambda: iniciar_ferias(_ctx),
)
botao_ferias.pack(side="left", padx=(0, 8))

botao_atestado = ctk.CTkButton(
    frame_lancar,
    text="Lançar atestados",
    font=_fonte_botao,
    fg_color=_LARANJA,
    hover_color=_LARANJA_HV,
    text_color=_TXT_INV,
    corner_radius=4,
    height=36,
    command=lambda: iniciar_atestado(_ctx),
)
botao_atestado.pack(side="left", padx=(0, 8))

botao_importar_base = ctk.CTkButton(
    frame_lancar,
    text="Importar Base de Treinamentos",
    font=_fonte_botao,
    fg_color=_CHUMBO,
    hover_color=_CHUMBO_2,
    text_color=_TXT_INV,
    corner_radius=4,
    height=36,
    command=lambda: iniciar_importar_base_treinamentos(_ctx),
)
botao_importar_base.pack(side="left")

frame_validacao = ctk.CTkFrame(painel_botoes, fg_color=_PAINEL, corner_radius=0)

botao_validar = ctk.CTkButton(
    frame_validacao,
    text="Validar distribuição",
    font=_fonte_botao,
    fg_color=_LARANJA,
    hover_color=_LARANJA_HV,
    text_color=_TXT_INV,
    corner_radius=4,
    height=36,
    command=lambda: iniciar_validacao(_ctx),
)
botao_validar.pack(side="left", padx=(0, 8))

botao_validar_hr = ctk.CTkButton(
    frame_validacao,
    text="Validar Hr Trabalhadas",
    font=_fonte_botao,
    fg_color=_LARANJA,
    hover_color=_LARANJA_HV,
    text_color=_TXT_INV,
    corner_radius=4,
    height=36,
    command=lambda: iniciar_validar_hr(_ctx),
)
botao_validar_hr.pack(side="left")

frame_lancar.pack(padx=16, pady=12, fill="x")

ctk.CTkLabel(
    content,
    text="Log de execução",
    font=_fonte_label,
    text_color="#5a5a5a",
    anchor="w",
).pack(padx=16, pady=(8, 4), anchor="w")

area_saida = ctk.CTkTextbox(
    content,
    font=_fonte_log,
    fg_color="#f4f4f4",
    text_color=_CHUMBO,
    corner_radius=4,
    border_width=1,
    border_color="#d9d9d9",
    wrap="word",
)
area_saida.pack(fill="both", expand=True, padx=16, pady=(0, 16))


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
