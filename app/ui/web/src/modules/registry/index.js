// Wrappers de fetch para /api/registry/<tipo>. Single source of truth para
// chamar o backend de registro de paths.

async function fetchJSON(url, init) {
  const r = await fetch(url, init);
  if (!r.ok) {
    let msg = r.statusText;
    try { const j = await r.json(); msg = j.detail || j.message || msg; } catch { /* ignore */ }
    const err = new Error(msg); err.code = `HTTP_${r.status}`; throw err;
  }
  return r.json();
}

export function registrar(tipo, caminho) {
  return fetchJSON(`/api/registry/${tipo}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ caminho }),
  });
}

export function consultar(tipo) {
  return fetchJSON(`/api/registry/${tipo}`);
}

// Ponte para o dialog nativo via pywebview. Em browser puro retorna
// null com aviso (dev only).
export async function escolherArquivoNativo(titulo) {
  if (!window.pywebview?.api?.escolher_arquivo) {
    // Fallback dev: usa <input type="file"> oculto e retorna null para
    // sinalizar que UX nativa não está disponível. Em produção o build
    // empacotado garante pywebview presente.
    return null;
  }
  return await window.pywebview.api.escolher_arquivo(titulo);
}
