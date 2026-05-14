import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Modal, FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Print   from 'expo-print';
import * as Sharing from 'expo-sharing';
import { useNavigation } from '@react-navigation/native';

import { Colors }    from '../../constants/colors';
import { etatsApi }  from '../../api/etats';
import type { StockOuvertureResponse, StockOuvertureLigne, Periode } from '../../api/etats';

// ── Helpers ───────────────────────────────────────────────────────

function fmtN(v: number | string | null | undefined, dec = 0): string {
  const n = Number(v);
  if (isNaN(n)) return '0';
  return n.toLocaleString('fr-FR', {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  });
}

// ── PDF HTML ──────────────────────────────────────────────────────

function buildHtml(data: StockOuvertureResponse): string {
  const rows = data.lignes.map((l, i) => `
    <tr${i % 2 === 1 ? ' class="alt"' : ''}>
      <td>
        <span style="background:#0E2A47;color:#FFF;padding:1px 6px;border-radius:4px;font-weight:700;font-size:9px">
          ${l.produit_sigle}
        </span>
        &nbsp;${l.produit_nom}
      </td>
      <td class="r" style="font-weight:700">${fmtN(l.stock_ouverture)}</td>
      <td class="r" style="color:#1F9D55;font-weight:700">${fmtN(l.entrees)}</td>
      <td class="r" style="color:#D63B3B;font-weight:700">${fmtN(l.sorties)}</td>
      <td class="r" style="color:#0E2A47;font-weight:800">${fmtN(l.stock_fermeture)}</td>
    </tr>`).join('');

  return `<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;font-size:10px;color:#0B1220;padding:20px 24px}
.ph{background:#0E2A47;color:#FFF;border-radius:10px;padding:16px 20px;margin-bottom:18px}
.ph-title{font-size:18px;font-weight:800}
.ph-sub{font-size:11px;opacity:.75;margin-top:2px}
.badge{display:inline-block;background:#E67A2A;color:#FFF;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:800;margin-bottom:4px}
.ph-right{float:right;text-align:right}
.kpi{display:table;width:100%;margin-bottom:18px;border-spacing:10px 0}
.k{display:table-cell;width:25%;background:#E8EEF6;border-radius:8px;padding:10px 12px}
.k-lbl{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6B7589}
.k-val{font-size:15px;font-weight:800;color:#0B1220;margin:3px 0 1px}
.sec{font-size:11px;font-weight:800;color:#0E2A47;margin:18px 0 6px;padding-bottom:4px;border-bottom:2px solid #0E2A47;text-transform:uppercase;letter-spacing:.5px}
table{width:100%;border-collapse:collapse}
thead tr{background:#0E2A47}
thead th{color:#FFF;padding:7px 8px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;text-align:left}
thead th.r{text-align:right}
tbody td{padding:6px 8px;font-size:10px;border-bottom:1px solid #EFF2F7}
tbody td.r{text-align:right}
tr.alt{background:#F7F8FB}
tfoot td{background:#0E2A47;color:#FFF;font-weight:700;padding:7px 8px;font-size:10px}
tfoot td.r{text-align:right}
.footer{margin-top:24px;text-align:center;font-size:9px;color:#A8B0BF;border-top:1px solid #EFF2F7;padding-top:10px}
</style></head><body>
<div class="ph">
  <div class="ph-right">
    <div class="badge">STOCK OUV/FERM</div><br/>
    <strong>${data.marketeur_nom}</strong>
  </div>
  <div class="ph-title">STOCK OUVERTURE / FERMETURE</div>
  <div class="ph-sub">Système de Gestion des Dépôts Pétroliers</div>
  <div class="ph-sub" style="margin-top:8px">${data.periode_nom}</div>
</div>
<div class="kpi">
  <div class="k"><div class="k-lbl">Stock Ouverture</div><div class="k-val">${fmtN(data.total_ouverture)}</div><div style="font-size:9px;color:#6B7589">litres</div></div>
  <div class="k" style="background:#D8F3E2"><div class="k-lbl">Entrées</div><div class="k-val" style="color:#1F9D55">${fmtN(data.total_entrees)}</div><div style="font-size:9px;color:#6B7589">litres</div></div>
  <div class="k" style="background:#FBE0E0"><div class="k-lbl">Sorties</div><div class="k-val" style="color:#D63B3B">${fmtN(data.total_sorties)}</div><div style="font-size:9px;color:#6B7589">litres</div></div>
  <div class="k"><div class="k-lbl">Stock Fermeture</div><div class="k-val" style="color:#0E2A47">${fmtN(data.total_fermeture)}</div><div style="font-size:9px;color:#6B7589">litres</div></div>
</div>
<div class="sec">Détail par produit</div>
<table>
  <thead><tr>
    <th>Produit</th>
    <th class="r">Ouverture (L)</th>
    <th class="r">Entrées (L)</th>
    <th class="r">Sorties (L)</th>
    <th class="r">Fermeture (L)</th>
  </tr></thead>
  <tbody>${rows}</tbody>
  <tfoot><tr>
    <td>TOTAUX</td>
    <td class="r">${fmtN(data.total_ouverture)}</td>
    <td class="r">${fmtN(data.total_entrees)}</td>
    <td class="r">${fmtN(data.total_sorties)}</td>
    <td class="r">${fmtN(data.total_fermeture)}</td>
  </tr></tfoot>
</table>
<div class="footer">Généré le ${new Date().toLocaleDateString('fr-FR')} · SGDS Mobile v2.0 · ${data.marketeur_nom}</div>
</body></html>`;
}

// ── Composant ─────────────────────────────────────────────────────

export function StockOuvertureScreen() {
  const navigation = useNavigation();

  const [data,        setData]        = useState<StockOuvertureResponse | null>(null);
  const [periodes,    setPeriodes]    = useState<Periode[]>([]);
  const [selectedPer, setSelectedPer] = useState<Periode | null>(null);
  const [loading,     setLoading]     = useState(true);
  const [exporting,   setExporting]   = useState(false);
  const [showModal,   setShowModal]   = useState(false);

  // Charger les périodes
  useEffect(() => {
    etatsApi.periodes()
      .then(r => setPeriodes(r.data))
      .catch(() => {});
  }, []);

  // Charger les données quand la période change
  const load = useCallback(async (periodeId?: number) => {
    setLoading(true);
    try {
      const r = await etatsApi.stockOuverture(periodeId);
      setData(r.data);
    } catch (e) {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(selectedPer?.id);
  }, [selectedPer]);

  // Export PDF
  const exportPdf = async () => {
    if (!data) return;
    setExporting(true);
    try {
      const html  = buildHtml(data);
      const { uri } = await Print.printToFileAsync({ html });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, { mimeType: 'application/pdf', dialogTitle: 'Stock Ouv/Ferm' });
      } else {
        await Print.printAsync({ html });
      }
    } catch (e) {
      console.warn('PDF export error', e);
    } finally {
      setExporting(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <LinearGradient
        colors={[Colors.navySoft, Colors.navy, Colors.navyDeep]}
        style={styles.hero}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
      >
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color={Colors.white} />
        </TouchableOpacity>
        <View style={styles.heroContent}>
          <Text style={styles.heroSub}>État</Text>
          <Text style={styles.heroTitle}>Stock Ouverture / Fermeture</Text>
          {data && <Text style={styles.heroPeriode}>{data.periode_nom}</Text>}
        </View>
        <TouchableOpacity style={styles.pdfBtn} onPress={exportPdf} disabled={exporting || !data}>
          {exporting
            ? <ActivityIndicator size="small" color={Colors.white} />
            : <Ionicons name="share-outline" size={20} color={Colors.white} />}
        </TouchableOpacity>
      </LinearGradient>

      {/* Sélecteur de période */}
      <View style={styles.filterRow}>
        <TouchableOpacity style={styles.perBtn} onPress={() => setShowModal(true)}>
          <Ionicons name="calendar-outline" size={14} color={Colors.navy} />
          <Text style={styles.perBtnText}>{selectedPer ? selectedPer.nom : 'Période courante'}</Text>
          <Ionicons name="chevron-down" size={14} color={Colors.slate} />
        </TouchableOpacity>
        {selectedPer && (
          <TouchableOpacity onPress={() => setSelectedPer(null)} style={styles.clearBtn}>
            <Ionicons name="close-circle" size={18} color={Colors.slate} />
          </TouchableOpacity>
        )}
      </View>

      {/* Contenu */}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.navy} />
        </View>
      ) : !data || data.lignes.length === 0 ? (
        <View style={styles.center}>
          <Ionicons name="layers-outline" size={48} color={Colors.silver} />
          <Text style={styles.emptyText}>Aucun mouvement pour cette période</Text>
        </View>
      ) : (
        <ScrollView style={styles.scroll} contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}>

          {/* KPI globaux */}
          <View style={styles.kpiRow}>
            <View style={[styles.kpiCard, { backgroundColor: Colors.navyTint }]}>
              <Text style={styles.kpiLabel}>Ouverture</Text>
              <Text style={[styles.kpiValue, { color: Colors.navy }]}>
                {fmtN(data.total_ouverture)}
              </Text>
              <Text style={styles.kpiUnit}>L</Text>
            </View>
            <View style={[styles.kpiCard, { backgroundColor: Colors.greenSoft }]}>
              <Text style={styles.kpiLabel}>Entrées</Text>
              <Text style={[styles.kpiValue, { color: Colors.entree }]}>
                {fmtN(data.total_entrees)}
              </Text>
              <Text style={styles.kpiUnit}>L</Text>
            </View>
            <View style={[styles.kpiCard, { backgroundColor: '#FBE0E0' }]}>
              <Text style={styles.kpiLabel}>Sorties</Text>
              <Text style={[styles.kpiValue, { color: Colors.sortie }]}>
                {fmtN(data.total_sorties)}
              </Text>
              <Text style={styles.kpiUnit}>L</Text>
            </View>
          </View>

          {/* Stock fermeture total */}
          <View style={styles.fermCard}>
            <View>
              <Text style={styles.fermLabel}>Stock de Fermeture Total</Text>
              <Text style={styles.fermSub}>{data.lignes.length} produit(s) — {data.periode_nom}</Text>
            </View>
            <Text style={styles.fermValue}>{fmtN(data.total_fermeture)} L</Text>
          </View>

          {/* Tableau par produit */}
          <Text style={styles.sectionTitle}>DÉTAIL PAR PRODUIT</Text>
          {data.lignes.map((l, i) => (
            <ProduitRow key={l.produit_id} ligne={l} index={i} />
          ))}

          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>TOTAUX</Text>
            <View style={styles.totalCols}>
              <ColVal label="Ouverture" value={data.total_ouverture} color={Colors.navy} />
              <ColVal label="Entrées"   value={data.total_entrees}   color={Colors.entree} />
              <ColVal label="Sorties"   value={data.total_sorties}   color={Colors.sortie} />
              <ColVal label="Fermeture" value={data.total_fermeture} color={Colors.navy} bold />
            </View>
          </View>
        </ScrollView>
      )}

      {/* Modal sélection période */}
      <Modal visible={showModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalBox}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Choisir une période</Text>
              <TouchableOpacity onPress={() => setShowModal(false)}>
                <Ionicons name="close" size={22} color={Colors.ink} />
              </TouchableOpacity>
            </View>
            <FlatList
              data={periodes}
              keyExtractor={p => String(p.id)}
              renderItem={({ item: p }) => (
                <TouchableOpacity
                  style={[styles.perItem, selectedPer?.id === p.id && styles.perItemActive]}
                  onPress={() => { setSelectedPer(p); setShowModal(false); }}
                >
                  <Text style={[styles.perItemText, selectedPer?.id === p.id && { color: Colors.white }]}>
                    {p.nom}
                  </Text>
                  {p.statut === 'OUVERTE' && (
                    <View style={styles.openBadge}>
                      <Text style={styles.openBadgeText}>OUVERTE</Text>
                    </View>
                  )}
                </TouchableOpacity>
              )}
            />
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

// ── Sous-composants ───────────────────────────────────────────────

function ProduitRow({ ligne, index }: { ligne: StockOuvertureLigne; index: number }) {
  const bg = index % 2 === 1 ? '#F7F8FB' : Colors.white;
  return (
    <View style={[styles.prodRow, { backgroundColor: bg }]}>
      <View style={styles.prodHeader}>
        <View style={styles.sigleBadge}>
          <Text style={styles.sigleText}>{ligne.produit_sigle}</Text>
        </View>
        <Text style={styles.prodNom}>{ligne.produit_nom}</Text>
      </View>
      <View style={styles.prodCols}>
        <ColVal label="Ouverture" value={ligne.stock_ouverture} color={Colors.navy} />
        <ColVal label="Entrées"   value={ligne.entrees}         color={Colors.entree} />
        <ColVal label="Sorties"   value={ligne.sorties}         color={Colors.sortie} />
        <ColVal label="Fermeture" value={ligne.stock_fermeture} color={Colors.navy} bold />
      </View>
    </View>
  );
}

function ColVal({ label, value, color, bold }: {
  label: string; value: number; color: string; bold?: boolean;
}) {
  return (
    <View style={styles.colVal}>
      <Text style={styles.colLabel}>{label}</Text>
      <Text style={[styles.colValue, { color }, bold && { fontSize: 14 }]}>
        {fmtN(value)}
      </Text>
      <Text style={styles.colUnit}>L</Text>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe:  { flex: 1, backgroundColor: Colors.paper },
  hero: {
    paddingHorizontal: 16, paddingTop: 10, paddingBottom: 18,
    flexDirection: 'row', alignItems: 'center',
  },
  backBtn:    { marginRight: 10, padding: 4 },
  heroContent: { flex: 1 },
  heroSub:    { color: Colors.white + 'bf', fontSize: 10, fontWeight: '600', letterSpacing: 0.5 },
  heroTitle:  { color: Colors.white, fontSize: 18, fontWeight: '800', letterSpacing: -0.3 },
  heroPeriode: { color: Colors.white + 'b3', fontSize: 11, marginTop: 2 },
  pdfBtn: {
    width: 38, height: 38, borderRadius: 12,
    backgroundColor: Colors.white + '22',
    alignItems: 'center', justifyContent: 'center',
  },

  filterRow: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 10,
    backgroundColor: Colors.white,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
    gap: 8,
  },
  perBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center',
    gap: 6, backgroundColor: Colors.navyTint,
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8,
  },
  perBtnText: { flex: 1, fontSize: 13, fontWeight: '600', color: Colors.navy },
  clearBtn:   { padding: 4 },

  scroll:   { flex: 1 },
  content:  { padding: 16, paddingBottom: 40 },
  center:   { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  emptyText: { fontSize: 14, color: Colors.slate, textAlign: 'center' },

  kpiRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  kpiCard: {
    flex: 1, borderRadius: 12, padding: 10, alignItems: 'center',
  },
  kpiLabel: { fontSize: 9, fontWeight: '700', color: Colors.slate, textTransform: 'uppercase', letterSpacing: 0.3 },
  kpiValue: { fontSize: 16, fontWeight: '800', marginTop: 2 },
  kpiUnit:  { fontSize: 9, color: Colors.slate },

  fermCard: {
    backgroundColor: Colors.navy, borderRadius: 14,
    padding: 14, marginBottom: 16,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
  },
  fermLabel: { color: Colors.white, fontSize: 13, fontWeight: '700' },
  fermSub:   { color: Colors.white + 'b3', fontSize: 11, marginTop: 2 },
  fermValue: { color: Colors.white, fontSize: 20, fontWeight: '800' },

  sectionTitle: {
    fontSize: 10, fontWeight: '800', color: Colors.slate,
    textTransform: 'uppercase', letterSpacing: 0.5,
    marginBottom: 8, marginTop: 4,
  },

  prodRow: {
    borderRadius: 10, padding: 12, marginBottom: 6,
    borderWidth: 1, borderColor: Colors.cloud,
  },
  prodHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 },
  sigleBadge: {
    backgroundColor: Colors.navy, borderRadius: 6,
    paddingHorizontal: 7, paddingVertical: 2,
  },
  sigleText: { color: Colors.white, fontSize: 9, fontWeight: '700' },
  prodNom:   { fontSize: 13, fontWeight: '700', color: Colors.ink, flex: 1 },

  prodCols: { flexDirection: 'row', gap: 4 },
  colVal:   { flex: 1, alignItems: 'center' },
  colLabel: { fontSize: 9, color: Colors.slate, textTransform: 'uppercase', letterSpacing: 0.3 },
  colValue: { fontSize: 13, fontWeight: '700', marginTop: 1 },
  colUnit:  { fontSize: 9, color: Colors.silver },

  totalRow: {
    backgroundColor: Colors.navy, borderRadius: 12,
    padding: 12, marginTop: 4,
  },
  totalLabel: { color: Colors.white, fontSize: 10, fontWeight: '700', letterSpacing: 0.5, marginBottom: 8 },
  totalCols:  { flexDirection: 'row', gap: 4 },

  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalBox: {
    backgroundColor: Colors.white, borderTopLeftRadius: 20, borderTopRightRadius: 20,
    maxHeight: '70%', paddingBottom: 24,
  },
  modalHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    padding: 16, borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  modalTitle: { fontSize: 16, fontWeight: '800', color: Colors.ink },
  perItem: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
    gap: 10,
  },
  perItemActive: { backgroundColor: Colors.navy },
  perItemText: { flex: 1, fontSize: 14, fontWeight: '600', color: Colors.ink },
  openBadge: {
    backgroundColor: Colors.greenSoft, borderRadius: 6,
    paddingHorizontal: 6, paddingVertical: 2,
  },
  openBadgeText: { fontSize: 9, fontWeight: '700', color: Colors.entree },
});
