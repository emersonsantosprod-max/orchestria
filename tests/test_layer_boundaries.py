"""Enforcement de fronteiras de camadas (CLAUDE.md → ARCHITECTURE).

Regras checadas via AST estático sobre os módulos já migrados:
  - app/domain/* não importa sqlite3, openpyxl, app.application, app.infrastructure.
  - app/application/services/* não importa app.infrastructure (services
    dependem de ports, não de adapters).

Exceção intencional: app/application/pipeline.py é o orquestrador
multi-domínio e atua como ponto de composição que constrói adapters
para passar a services. Aplicar a mesma regra estrita a ele exigiria
introduzir um port para cada dependência (ferias, atestado, excel, db),
o que viola o cap "um port por refactor" e adiciona indireção sem
ganho de testabilidade. Pipeline fica fora deste teste enquanto não
houver justificativa para mais ports.

Módulos legacy ainda flat em app/*.py (ferias, atestado, distribuicao,
validar_*) ficam fora de escopo desta janela de migração — ver
PROJECT_STRUCTURE.md.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN_DIR = ROOT / "app" / "domain"
APPLICATION_SERVICES_DIR = ROOT / "app" / "application" / "services"
MAIN_FILE = ROOT / "app" / "main.py"


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    nomes: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            nomes.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            nomes.append(node.module)
    return nomes


def _python_files(diretorio: Path) -> list[Path]:
    return sorted(p for p in diretorio.rglob("*.py") if p.name != "__pycache__")


def _violacoes(arquivo: Path, proibidos: tuple[str, ...]) -> list[tuple[Path, str]]:
    erros: list[tuple[Path, str]] = []
    for nome in _imports(arquivo):
        for proibido in proibidos:
            if nome == proibido or nome.startswith(proibido + "."):
                erros.append((arquivo, nome))
    return erros


def test_app_domain_nao_importa_sqlite_openpyxl_application_infrastructure():
    proibidos = ("sqlite3", "openpyxl", "app.application", "app.infrastructure")
    erros: list[tuple[Path, str]] = []
    for arquivo in _python_files(DOMAIN_DIR):
        erros.extend(_violacoes(arquivo, proibidos))
    assert not erros, "violação de fronteira em app/domain/:\n" + "\n".join(
        f"  {p.relative_to(ROOT)}: importa {n}" for p, n in erros
    )


def test_app_application_services_nao_importa_app_infrastructure():
    proibidos = ("app.infrastructure",)
    erros: list[tuple[Path, str]] = []
    for arquivo in _python_files(APPLICATION_SERVICES_DIR):
        erros.extend(_violacoes(arquivo, proibidos))
    assert not erros, "violação de fronteira em app/application/services/:\n" + "\n".join(
        f"  {p.relative_to(ROOT)}: importa {n}" for p, n in erros
    )


def test_main_nao_importa_app_domain():
    """CLI wrapper (main.py) não pode conhecer módulos de domínio.

    Features são expostas exclusivamente via parâmetros do
    pipeline.executar_pipeline. Importar app.domain.* em main.py
    indicaria que CLI ganhou conhecimento de regra de negócio —
    regressão arquitetural a ser bloqueada no CI.
    """
    erros = _violacoes(MAIN_FILE, ("app.domain",))
    assert not erros, "main.py não pode importar app.domain.*:\n" + "\n".join(
        f"  {p.relative_to(ROOT)}: importa {n}" for p, n in erros
    )
