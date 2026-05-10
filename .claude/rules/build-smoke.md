## Build Smoke — PyInstaller bundle validation

Procedimento canônico para empacotar `AutomacaoMedicao.spec` e validar
o `.exe` no host Windows. Roda **antes** de fechar qualquer entrega que
toca `app/desktop_entry.py`, `AutomacaoMedicao.spec`, rotas do FastAPI,
ou o frontend Vite.

### Pré-requisitos no host Windows

1. `venv_win` ativo (ou venv equivalente com Python 3.11+).
2. **pywebview instalado**: `pip install -e .` na raiz do projeto (resolve
   via `pyproject.toml`), ou `pip install pywebview==5.4` explícito.
   O `.spec` aborta cedo com mensagem clara se o pacote estiver ausente
   (linhas iniciais do `Analysis` block).
3. WebView2 Runtime instalado no Windows (Win10 1809+ ou Win11 nativos;
   instalável via `MicrosoftEdgeWebView2RuntimeInstallerX64.exe`).
4. `npm run build` em `app/ui/web/` para gerar `app/ui/web/dist/`.

### Comando de build

```bash
pyinstaller AutomacaoMedicao.spec
```

Output: `dist/AutomacaoMedicao.exe`.

### Hidden imports load-bearing

Conforme [AutomacaoMedicao.spec](../../AutomacaoMedicao.spec):
- `collect_submodules('webview')` cobre o grosso do pacote pywebview.
- Explícitos adicionais (`hiddenimports`): `webview.platforms.edgechromium`
  + `proxy_tools` — backend default em Win10+ e sua dependência direta.
- **Não adicionar** `clr`/`System`/`webview.platforms.winforms` sem
  confirmação de que o backend ativo é winforms (não é o default).

### Smoke checklist (executar `.exe` no Windows)

1. `.exe` inicia → SPA renderiza sem tela branca.
2. Botão "Selecionar arquivo" em Configurações → dialog nativo do SO abre.
3. Registrar medição + 4 bases (treinamentos, cobrança, tags, distribuição)
   → cards mostram caminho selecionado.
4. Executar 1 módulo (ex: férias) → arquivo gerado em `data/exports/`.
5. Fechar e reabrir `.exe` → registry persiste, UI consistente, paths
   válidos (ou marcam "ausente" se o usuário moveu o arquivo no SO).
6. `Executar Férias` bloqueado sem `base_tags` registrada; desbloqueado
   após registrar.
7. Mover/deletar um arquivo registrado no SO → tentar executar → erro
   404 ARQUIVO_NAO_ENCONTRADO claro.

### Critério "smoke passed"

Todos os 7 itens da checklist OK + zero `ModuleNotFoundError` no console
do `.exe`. Registrar em `.claude/SESSION_STATE.md` na linha de status:
`smoke 4b passed (build: <data>)` com a versão de pywebview e Windows
testados.

### Falha mode comum: ModuleNotFoundError em runtime

Se o `.exe` levantar `No module named 'webview'`:
- Causa raiz: pywebview ausente do venv usado para build. **Não** é
  problema de hiddenimports — `collect_submodules` retorna lista vazia
  silenciosamente quando o pacote não está instalado.
- Fix: `pip install -e .` no venv de build e rebuild. O `.spec` agora
  falha antes da Analysis com mensagem clara nesse caso.

Se o `.exe` levantar `No module named 'webview.platforms.X'`:
- Causa: backend específico (X = winforms, qt, cef) ativado em runtime
  mas não bundleado. Confirmar qual backend o pywebview escolheu via
  log do `.exe` (ou `webview.config.gui` se houver config explícita).
- Fix: adicionar `'webview.platforms.X'` + deps específicas
  (`clr`+`System` para winforms; `cefpython3` para cef; PyQt para qt)
  em `hiddenimports` na `.spec`.
