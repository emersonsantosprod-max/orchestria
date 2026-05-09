// Pure formatters — no JSX, no React imports.

export function fmtMes(yyyymm) {
  if (!yyyymm) return '';
  const [y, m] = yyyymm.split('-');
  const meses = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
  return `${meses[parseInt(m, 10) - 1]} · ${y}`;
}

export function fmtRelative(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return 'agora';
  if (diff < 3600) return `há ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `há ${Math.floor(diff / 3600)} h`;
  return d.toLocaleDateString('pt-BR');
}
