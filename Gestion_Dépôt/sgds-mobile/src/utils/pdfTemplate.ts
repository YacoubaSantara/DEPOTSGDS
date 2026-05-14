/**
 * Templates HTML pour la génération de PDF via expo-print.
 * Utilise uniquement HTML/CSS inline sans dépendances externes.
 */

import { StockLigne, RecapProduit, RecapTotaux } from '../api/etats';

// ── Formatage ─────────────────────────────────────────────────────

/** Formate un nombre avec espace comme séparateur des milliers (style fr-FR) */
function fmtN(n: number | string | null | undefined, dec = 0): string {
  const v = Number(n);
  if (isNaN(v) || v === 0) return dec > 0 ? '0' : '0';
  const factor = Math.pow(10, dec);
  const rounded = Math.round(v * factor) / factor;
  const parts = rounded.toFixed(dec).split('.');
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' '); // espace insécable
  return dec > 0 ? parts.join(',') : parts[0];
}

const TYPE_LABELS: Record<string, string> = {
  ENTREE: 'Entrée',
  SORTIE: 'Sortie',
  CESSION: 'Cession',
  ACQUITTEMENT: 'Acquitt.',
};

const TYPE_COLORS: Record<string, string> = {
  ENTREE: '#1F9D55',
  SORTIE: '#D63B3B',
  CESSION: '#6E47C7',
  ACQUITTEMENT: '#1497B8',
};

function fmtDate(d: string): string {
  if (!d || d.length < 10) return '—';
  return d.slice(8, 10) + '/' + d.slice(5, 7) + '/' + d.slice(0, 4);
}

// ── CSS commun ────────────────────────────────────────────────────

const BASE_CSS = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10px;
    color: #0B1220;
    padding: 20px 24px;
    background: #FFFFFF;
  }
  .page-header {
    background: #0E2A47;
    color: #FFFFFF;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 18px;
    overflow: hidden;
    position: relative;
  }
  .page-header::after {
    content: '';
    position: absolute;
    right: -40px; top: -40px;
    width: 160px; height: 160px;
    border-radius: 50%;
    background: rgba(230,122,42,0.18);
  }
  .ph-title { font-size: 18px; font-weight: 800; letter-spacing: -0.5px; }
  .ph-sub   { font-size: 11px; opacity: 0.75; margin-top: 2px; }
  .ph-right { float: right; text-align: right; }
  .badge {
    display: inline-block;
    background: #E67A2A;
    color: #FFF;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 4px;
  }
  .summary-row {
    display: table;
    width: 100%;
    margin-bottom: 18px;
    border-spacing: 10px 0;
  }
  .sum-card {
    display: table-cell;
    width: 33.33%;
    border-radius: 8px;
    padding: 10px 12px;
    vertical-align: top;
  }
  .sum-card.navy  { background: #E8EEF6; }
  .sum-card.green { background: #D8F3E2; }
  .sum-card.red   { background: #FBE0E0; }
  .sum-label { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #6B7589; }
  .sum-value { font-size: 16px; font-weight: 800; color: #0B1220; margin: 3px 0 1px; }
  .sum-unit  { font-size: 9px; color: #6B7589; }
  .section-title {
    font-size: 11px; font-weight: 800; color: #0E2A47;
    margin: 18px 0 6px;
    padding-bottom: 4px;
    border-bottom: 2px solid #0E2A47;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  table { width: 100%; border-collapse: collapse; }
  thead tr { background: #0E2A47; }
  thead th {
    color: #FFF; padding: 7px 8px;
    font-size: 9px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.4px;
    text-align: left;
  }
  thead th.r { text-align: right; }
  tbody td { padding: 6px 8px; font-size: 10px; border-bottom: 1px solid #EFF2F7; }
  tbody td.r { text-align: right; }
  tr.alt { background: #F7F8FB; }
  tfoot td {
    background: #0E2A47; color: #FFF;
    font-weight: 700; padding: 7px 8px;
    font-size: 10px;
  }
  tfoot td.r { text-align: right; }
  .footer {
    margin-top: 24px;
    text-align: center;
    font-size: 9px;
    color: #A8B0BF;
    border-top: 1px solid #EFF2F7;
    padding-top: 10px;
  }
`;

// ── Carte de Stock PDF ────────────────────────────────────────────

export interface CarteStockPdfParams {
  marketeurNom: string;
  produitNom: string;
  produitSigle: string;
  periodeLabel: string;
  lignes: StockLigne[];
  cumul_entrees_ambiant: number;
  cumul_sorties_ambiant: number;
  stock_final_ambiant: number;
  stock_final_15: number;
  generatedAt: string;
}

export function buildCarteStockHtml(p: CarteStockPdfParams): string {
  const rows = p.lignes.map((l, i) => {
    const dt    = fmtDate(l.date);
    const type  = TYPE_LABELS[l.type] ?? l.type;
    const color = TYPE_COLORS[l.type] ?? '#6B7589';
    const hasIn  = Number(l.entree_ambiant) > 0;
    const hasOut = Number(l.sortie_ambiant) > 0;
    return `
      <tr${i % 2 === 1 ? ' class="alt"' : ''}>
        <td>${dt}</td>
        <td>${l.reference || '—'}</td>
        <td style="color:${color};font-weight:700">${type}</td>
        <td class="r" style="color:#1F9D55;font-weight:${hasIn ? '700' : '400'}">
          ${hasIn ? fmtN(l.entree_ambiant) : '<span style="color:#A8B0BF">—</span>'}
        </td>
        <td class="r" style="color:#D63B3B;font-weight:${hasOut ? '700' : '400'}">
          ${hasOut ? fmtN(l.sortie_ambiant) : '<span style="color:#A8B0BF">—</span>'}
        </td>
        <td class="r" style="font-weight:700">${fmtN(l.stock_ambiant)}</td>
      </tr>`;
  }).join('');

  const sigle = p.produitSigle || p.produitNom.slice(0, 4).toUpperCase();

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>${BASE_CSS}</style>
</head>
<body>
  <div class="page-header">
    <div class="ph-right">
      <div class="badge">${sigle}</div><br/>
      <strong>${p.produitNom}</strong><br/>
      <span style="font-size:10px;opacity:0.8">${p.marketeurNom}</span>
    </div>
    <div class="ph-title">CARTE DE STOCK</div>
    <div class="ph-sub">Système de Gestion des Dépôts Pétroliers</div>
    <div class="ph-sub" style="margin-top:8px">${p.periodeLabel}</div>
  </div>

  <div class="summary-row">
    <div class="sum-card navy">
      <div class="sum-label">Stock final (ambiant)</div>
      <div class="sum-value">${fmtN(p.stock_final_ambiant)}</div>
      <div class="sum-unit">litres</div>
    </div>
    <div class="sum-card green">
      <div class="sum-label">Total Entrées</div>
      <div class="sum-value">${fmtN(p.cumul_entrees_ambiant)}</div>
      <div class="sum-unit">litres ambiant</div>
    </div>
    <div class="sum-card red">
      <div class="sum-label">Total Sorties</div>
      <div class="sum-value">${fmtN(p.cumul_sorties_ambiant)}</div>
      <div class="sum-unit">litres ambiant</div>
    </div>
  </div>

  <div class="section-title">Détail des mouvements — ${p.lignes.length} ligne(s)</div>
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Référence</th>
        <th>Type</th>
        <th class="r">Entrée (L)</th>
        <th class="r">Sortie (L)</th>
        <th class="r">Stock (L)</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
    <tfoot>
      <tr>
        <td colspan="3">TOTAUX CUMULÉS</td>
        <td class="r">${fmtN(p.cumul_entrees_ambiant)}</td>
        <td class="r">${fmtN(p.cumul_sorties_ambiant)}</td>
        <td class="r">${fmtN(p.stock_final_ambiant)}</td>
      </tr>
    </tfoot>
  </table>

  <div class="footer">
    Rapport généré le ${p.generatedAt} &nbsp;·&nbsp;
    SGDS Mobile v2.0 &nbsp;·&nbsp; ${p.marketeurNom}
  </div>
</body>
</html>`;
}

// ── Récapitulatif PDF ─────────────────────────────────────────────

export interface RecapPdfParams {
  marketeurNom: string;
  periodeLabel: string;
  par_produit: RecapProduit[];
  totaux: RecapTotaux;
  generatedAt: string;
}

export function buildRecapHtml(p: RecapPdfParams): string {
  const produitRows = p.par_produit.map((pr, i) => `
    <tr${i % 2 === 1 ? ' class="alt"' : ''}>
      <td>
        <span style="background:#0E2A47;color:#FFF;padding:1px 6px;border-radius:4px;font-weight:700;font-size:9px">
          ${pr.produit_sigle}
        </span>
        &nbsp;${pr.produit_nom}
      </td>
      <td class="r" style="color:#1F9D55;font-weight:700">
        ${pr.nb_entrees > 0 ? fmtN(pr.volume_entree_ambiant) : '<span style="color:#A8B0BF">—</span>'}
        ${pr.nb_entrees > 0 ? `<span style="color:#A8B0BF;font-size:8px"> (${pr.nb_entrees})</span>` : ''}
      </td>
      <td class="r" style="color:#D63B3B;font-weight:700">
        ${pr.nb_sorties > 0 ? fmtN(pr.volume_sortie_ambiant) : '<span style="color:#A8B0BF">—</span>'}
        ${pr.nb_sorties > 0 ? `<span style="color:#A8B0BF;font-size:8px"> (${pr.nb_sorties})</span>` : ''}
      </td>
      <td class="r" style="color:#6E47C7;font-weight:700">
        ${pr.nb_cessions > 0 ? fmtN(pr.volume_cession_ambiant) : '<span style="color:#A8B0BF">—</span>'}
        ${pr.nb_cessions > 0 ? `<span style="color:#A8B0BF;font-size:8px"> (${pr.nb_cessions})</span>` : ''}
      </td>
      <td class="r" style="font-weight:800;color:#0E2A47">${fmtN(pr.stock_final_ambiant)}</td>
    </tr>`).join('');

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>${BASE_CSS}</style>
</head>
<body>
  <div class="page-header">
    <div class="ph-right">
      <div class="badge">${p.par_produit.length} produit(s)</div><br/>
      <strong>${p.marketeurNom}</strong>
    </div>
    <div class="ph-title">RÉCAPITULATIF DES MOUVEMENTS</div>
    <div class="ph-sub">Système de Gestion des Dépôts Pétroliers</div>
    <div class="ph-sub" style="margin-top:8px">${p.periodeLabel}</div>
  </div>

  <div class="summary-row">
    <div class="sum-card navy">
      <div class="sum-label">Stock final global</div>
      <div class="sum-value">${fmtN(p.totaux.stock_final_ambiant)}</div>
      <div class="sum-unit">litres ambiant</div>
    </div>
    <div class="sum-card green">
      <div class="sum-label">Total Entrées</div>
      <div class="sum-value">${fmtN(p.totaux.volume_entree_ambiant)}</div>
      <div class="sum-unit">${p.totaux.nb_entrees} mouvement(s)</div>
    </div>
    <div class="sum-card red">
      <div class="sum-label">Total Sorties</div>
      <div class="sum-value">${fmtN(p.totaux.volume_sortie_ambiant)}</div>
      <div class="sum-unit">${p.totaux.nb_sorties} mouvement(s)</div>
    </div>
  </div>

  <div class="section-title">Synthèse par produit — ${p.totaux.nb_mouvements} mouvements au total</div>
  <table>
    <thead>
      <tr>
        <th>Produit</th>
        <th class="r">Entrées (L)</th>
        <th class="r">Sorties (L)</th>
        <th class="r">Cessions (L)</th>
        <th class="r">Stock final (L)</th>
      </tr>
    </thead>
    <tbody>${produitRows}</tbody>
    <tfoot>
      <tr>
        <td>TOTAUX</td>
        <td class="r">${fmtN(p.totaux.volume_entree_ambiant)}</td>
        <td class="r">${fmtN(p.totaux.volume_sortie_ambiant)}</td>
        <td class="r">${fmtN(p.totaux.volume_cession_ambiant)}</td>
        <td class="r">${fmtN(p.totaux.stock_final_ambiant)}</td>
      </tr>
    </tfoot>
  </table>

  ${p.totaux.nb_acquittements > 0 ? `
  <div class="section-title" style="margin-top:16px">Acquittements</div>
  <table>
    <thead>
      <tr>
        <th>Nb acquittements</th>
        <th class="r">Volume acquitté (L)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>${p.totaux.nb_acquittements}</td>
        <td class="r" style="color:#1497B8;font-weight:700">${fmtN(p.totaux.volume_acquit_ambiant)}</td>
      </tr>
    </tbody>
  </table>` : ''}

  <div class="footer">
    Rapport généré le ${p.generatedAt} &nbsp;·&nbsp;
    SGDS Mobile v2.0 &nbsp;·&nbsp; ${p.marketeurNom}
  </div>
</body>
</html>`;
}
