"""
ferias.py — Regras de negócio para processamento de férias.

Produz lista de Update (tipo='ferias') com row explícito e sobrescrever_obs=True,
e inconsistencias com origem='ferias'.

Regras detalhadas:
  - Pré-flight: o col_map deve conter situacao, md_cobranca e sg_funcao.
  - Seleciona "1° Férias" se Status-1° == 'Aprovado'; senão "2° Férias";
    senão skip silenciosamente (não gera inconsistência).
  - Período: 'dd/mm/yyyy a dd/mm/yyyy'. Falha → 'período inválido'.
  - Skip antes de qualquer lookup se o período não intersecta o mês.
  - Classificação por linha (com cache local):
      MD Cobranca ∈ {ADICIONAL, PACOTE, CUSTO MANSERV}
          situacao = 'FÉRIAS' + observação 'DD/MM a DD/MM - FÉRIAS'.
      Senão lookup de Sg Função em base_cobranca (UPPER):
          'FÉRIAS S/ DESC' → situacao = 'FÉRIAS S/ DESC' + obs com sufixo '(NÃO DESCONTA)'.
          outro            → situacao = 'FÉRIAS' + obs sem sufixo.
          ausente          → 'sg função não classificada' (1x por matrícula+sg).
  - Observação SEMPRE populada para todas as férias.
  - sobrescrever_obs=True sempre (replace explícito).

Erros detectados:
  - 'período inválido'
  - 'matrícula não encontrada'   (1x por entrada)
  - 'sg função não classificada' (1x por (matrícula, sg_funcao))
"""

import re
from datetime import date, timedelta

from app.domain.core import Update, inconsistencia, normalizar_matricula

_RE_PERIODO = re.compile(
    r'(\d{2})/(\d{2})/(\d{4})\s*a\s*(\d{2})/(\d{2})/(\d{4})$'
)

MD_COBRANCA_FERIAS_DIRETO = frozenset({'ADICIONAL', 'PACOTE', 'CUSTO MANSERV'})
CATEGORIA_SEM_DESCONTO = 'FÉRIAS S/ DESC'
SITUACAO_PADRAO = 'FÉRIAS'
SITUACAO_SEM_DESC = 'FÉRIAS S/ DESC'

_OBRIGATORIAS_FERIAS = ('situacao', 'md_cobranca', 'sg_funcao')


def parse_periodo(s):
    """'dd/mm/yyyy a dd/mm/yyyy' → (date, date). Lança ValueError."""
    if s is None:
        raise ValueError("período vazio")
    match = _RE_PERIODO.fullmatch(str(s).strip())
    if not match:
        raise ValueError(f"formato inválido: {s!r}")
    di, mi, yi, df, mf, yf = (int(x) for x in match.groups())
    ini = date(yi, mi, di)
    fim = date(yf, mf, df)
    if fim < ini:
        raise ValueError(f"período invertido: {s!r}")
    return ini, fim


def selecionar_ferias(p1, s1, p2, s2):
    """Retorna (periodo_str, '1' ou '2') do primeiro aprovado; None caso contrário."""
    if p1 and s1 and str(s1).strip().lower() == 'aprovado':
        return str(p1), '1'
    if p2 and s2 and str(s2).strip().lower() == 'aprovado':
        return str(p2), '2'
    return None


def formatar_observacao(ini, fim, com_sufixo):
    """'dd/mm a dd/mm - FÉRIAS' (+ ' (NÃO DESCONTA)' se com_sufixo)."""
    base = f"{ini.day:02d}/{ini.month:02d} a {fim.day:02d}/{fim.month:02d} - FÉRIAS"
    return base + " (NÃO DESCONTA)" if com_sufixo else base


def _classificar(md_cob, sg_fun, base_cobranca):
    """Pura. Retorna (tipo, com_sufixo, erro_or_None)."""
    if md_cob in MD_COBRANCA_FERIAS_DIRETO:
        return ('FERIAS_DIRETO', False, None)
    if not sg_fun:
        return ('SKIP', False, 'sg função não classificada')
    categoria = base_cobranca.get(sg_fun)
    if categoria is None:
        return ('SKIP', False, 'sg função não classificada')
    if categoria.strip().upper() == CATEGORIA_SEM_DESCONTO:
        return ('FERIAS_SD', True, None)
    return ('FERIAS', False, None)


def gerar_updates_ferias(
    dados_ferias,
    base_cobranca,
    medicao_por_matricula,
    md_cobranca_por_chave,
    sg_funcao_por_chave,
    mes_referencia,
    col_map,
):
    """
    Retorna (atualizacoes, inconsistencias).

      atualizacoes: list[Update] (tipo='ferias')
        - row preenchido (resolvido aqui; writer não consulta índice)
        - sobrescrever_obs=True (sempre)
        - situacao preenchida quando aplicável

      inconsistencias: list[Inconsistencia] (origem='ferias')
    """
    faltantes = [c for c in _OBRIGATORIAS_FERIAS if c not in col_map]
    if faltantes:
        raise RuntimeError(
            "Medição não contém colunas obrigatórias para férias: "
            + ", ".join(faltantes)
        )

    if mes_referencia.day != 1:
        mes_referencia = mes_referencia.replace(day=1)
    mes_ini = mes_referencia
    if mes_ini.month == 12:
        prox = date(mes_ini.year + 1, 1, 1)
    else:
        prox = date(mes_ini.year, mes_ini.month + 1, 1)
    mes_fim = prox - timedelta(days=1)

    atualizacoes = []
    inconsistencias = []

    classificacao_cache = {}
    sg_nao_class_emitido = set()

    for r in dados_ferias:
        linha = r.get('linha', '-')
        chapa_raw = r.get('chapa')
        sel = selecionar_ferias(r.get('p1'), r.get('s1'), r.get('p2'), r.get('s2'))
        if sel is None:
            continue
        periodo_str, _ord = sel

        try:
            ini, fim = parse_periodo(periodo_str)
        except ValueError:
            inconsistencias.append(inconsistencia(
                'ferias', linha=linha,
                matricula=chapa_raw if chapa_raw is not None else '',
                data=periodo_str, erro='período inválido',
            ))
            continue

        ini_efetivo = ini if ini > mes_ini else mes_ini
        fim_efetivo = fim if fim < mes_fim else mes_fim
        if ini_efetivo > fim_efetivo:
            continue

        matricula = normalizar_matricula(chapa_raw)
        linhas_med = medicao_por_matricula.get(matricula)
        if not linhas_med:
            inconsistencias.append(inconsistencia(
                'ferias', linha=linha, matricula=matricula,
                data=periodo_str, erro='matrícula não encontrada',
            ))
            continue

        obs_com_sufixo = formatar_observacao(ini, fim, com_sufixo=True)
        obs_sem_sufixo = formatar_observacao(ini, fim, com_sufixo=False)

        for data_obj, data_str, rows in linhas_med:
            if data_obj < ini_efetivo or data_obj > fim_efetivo:
                continue
            chave = (matricula, data_str)
            md_cob = md_cobranca_por_chave.get(chave, '')
            sg_fun = sg_funcao_por_chave.get(chave, '')

            cache_key = (md_cob, sg_fun)
            classif = classificacao_cache.get(cache_key)
            if classif is None:
                classif = _classificar(md_cob, sg_fun, base_cobranca)
                classificacao_cache[cache_key] = classif
            tipo, com_sufixo, erro = classif

            if tipo == 'SKIP':
                dedup_key = (matricula, sg_fun)
                if dedup_key not in sg_nao_class_emitido:
                    sg_nao_class_emitido.add(dedup_key)
                    inconsistencias.append(inconsistencia(
                        'ferias', linha=linha, matricula=matricula,
                        data=data_str, erro=erro,
                    ))
                continue

            if tipo == 'FERIAS_DIRETO':
                situacao = SITUACAO_PADRAO
                observacao = obs_sem_sufixo
            elif tipo == 'FERIAS_SD':
                situacao = SITUACAO_SEM_DESC
                observacao = obs_com_sufixo
            else:
                situacao = SITUACAO_PADRAO
                observacao = obs_sem_sufixo

            for row_idx in rows:
                atualizacoes.append(Update(
                    tipo='ferias',
                    matricula=matricula,
                    data=data_str,
                    observacao=observacao,
                    situacao=situacao,
                    sobrescrever_obs=True,
                    row=row_idx,
                ))

    return atualizacoes, inconsistencias
