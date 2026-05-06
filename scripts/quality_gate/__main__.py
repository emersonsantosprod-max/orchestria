"""CLI: python -m scripts.quality_gate [--update-baseline] [--paths app tests]."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from scripts.quality_gate.metrics import coletar_metricas_codigo
from scripts.quality_gate.report import avaliar_regressao, formatar_tabela
from scripts.quality_gate.violations import contar_violacoes_ruff

RAIZ_REPO = Path(__file__).resolve().parents[2]
BASELINE_DEFAULT = RAIZ_REPO / 'quality_baseline.json'


def coletar_metricas(paths: list[Path]) -> dict:
    metricas = coletar_metricas_codigo(paths)
    metricas['violations'] = contar_violacoes_ruff(paths)
    return metricas


def carregar_baseline(caminho: Path) -> dict:
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding='utf-8')).get('metrics', {})


def gravar_baseline(caminho: Path, metricas: dict) -> None:
    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'metrics': metricas,
    }
    caminho.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='quality-gate')
    parser.add_argument('--update-baseline', action='store_true')
    parser.add_argument('--paths', nargs='+', default=['app', 'tests'])
    parser.add_argument('--baseline-file', default=str(BASELINE_DEFAULT))
    args = parser.parse_args(argv)

    paths = [RAIZ_REPO / p for p in args.paths]
    baseline_path = Path(args.baseline_file)
    atual = coletar_metricas(paths)

    if args.update_baseline:
        gravar_baseline(baseline_path, atual)
        print(f'baseline atualizado: {baseline_path}')
        print(formatar_tabela(atual, atual))
        return 0

    baseline = carregar_baseline(baseline_path)
    if not baseline:
        print(
            f'baseline ausente em {baseline_path}.\n'
            'rode: python -m scripts.quality_gate --update-baseline',
            file=sys.stderr,
        )
        return 2

    print(formatar_tabela(baseline, atual))
    return 1 if avaliar_regressao(baseline, atual) else 0


if __name__ == '__main__':
    sys.exit(main())
