// Re-export de formatters para padronizar imports via `modules/`.
// Implementação canônica vive em `components/format.js` (legacy
// path) — manter aqui apenas o re-export por enquanto. Migração para
// movimentar o conteúdo é cosmética.
export { fmtMes, fmtRelative } from '../../components/format.js';
