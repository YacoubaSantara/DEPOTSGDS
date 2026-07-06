import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Modal, FlatList, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Print   from 'expo-print';
import * as Sharing from 'expo-sharing';
import { useNavigation, useFocusEffect } from '@react-navigation/native';

import { Colors }   from '../../constants/colors';
import { etatsApi } from '../../api/etats';
import type { CoulageResponse, CoulageLigne, Periode } from '../../api/etats';
import { plusieursDepots, libellePeriode } from '../../utils/periodes';

// ── Helpers ───────────────────────────────────────────────────────

function fmtN(v: number | string | null | undefined, dec = 0): string {
  const n = Number(v);
  if (isNaN(n)) return '0';
  return n.toLocaleString('fr-FR', {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  });
}

// ── PDF ───────────────────────────────────────────────────────────

function buildHtml(data: CoulageResponse, periodeNom?: string): string {
  // Grouper les lignes par période
  const periodesMap: Record<string, CoulageLigne[]> = {};
  data.lignes.forEach(l => {
    const cle = l.periode_depot ? `${l.periode_nom} — ${l.periode_depot}` : l.periode_nom;
    if (!periodesMap[cle]) periodesMap[cle] = [];
    periodesMap[cle].push(l);
  });

  const sections = Object.entries(periodesMap).map(([pNom, lignes]) => {
    const rows = lignes.map((l, i) => `
      <tr${i % 2 === 1 ? ' class="alt"' : ''}>
        <td>
          <span style="background:#0E2A47;color:#FFF;padding:1px 6px;border-radius:4px;font-weight:700;font-size:8px">
            ${l.produit_sigle}
          </span>
          &nbsp;${l.produit_nom}
        </td>
        <td class="r">${fmtN(l.brut_entree)}</td>
        <td class="r" style="color:#D63B3B">${fmtN(l.coul_entree)}</td>
        <td class="r" style="color:#1F9D55;font-weight:700">${fmtN(l.entree_nette)}</td>
        <td class="r">${fmtN(l.sortie)}</td>
        <td class="r">${fmtN(l.qp_coul)}</td>
        <td class="r" style="color:#6E47C7;font-weight:700">${fmtN(l.volume_sorti)}</td>
        <td class="r">${fmtN(l.prix_unitaire, 4)}</td>
        <td class="r" style="font-weight:800;color:#E67A2A">${fmtN(l.montant)}</td>
      </tr>`).join('');

    const totMontant = lignes.reduce((s, l) => s + Number(l.montant), 0);
    const totVolume  = lignes.reduce((s, l) => s + Number(l.volume_sorti), 0);

    return `
      <div class="sec">${pNom}</div>
      <table>
        <thead><tr>
          <th>Produit</th>
          <th class="r">B.Entrée</th>
          <th class="r">Coul.</th>
          <th class="r">E.Nette</th>
          <th class="r">Sortie</th>
          <th class="r">QP Coul.</th>
          <th class="r">Vol. Sorti</th>
          <th class="r">Prix/L</th>
          <th class="r">Montant</th>
        </tr></thead>
        <tbody>${rows}</tbody>
        <tfoot><tr>
          <td colspan="6">TOTAUX</td>
          <td class="r">${fmtN(totVolume)}</td>
          <td></td>
          <td class="r">${fmtN(totMontant)} FCFA</td>
        </tr></tfoot>
      </table>`;
  }).join('');

  return `<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;font-size:9px;color:#0B1220;padding:20px 24px}
.ph{background:#0E2A47;color:#FFF;border-radius:10px;padding:16px 20px;margin-bottom:18px}
.ph-title{font-size:18px;font-weight:800}
.ph-sub{font-size:11px;opacity:.75;margin-top:2px}
.badge{display:inline-block;background:#E67A2A;color:#FFF;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:800;margin-bottom:4px}
.ph-right{float:right;text-align:right}
.kpi{display:table;width:100%;margin-bottom:18px;border-spacing:10px 0}
.k{display:table-cell;width:50%;border-radius:8px;padding:10px 12px}
.k-lbl{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6B7589}
.k-val{font-size:18px;font-weight:800;margin:3px 0 1px}
.sec{font-size:11px;font-weight:800;color:#0E2A47;margin:18px 0 6px;padding-bottom:4px;border-bottom:2px solid #0E2A47;text-transform:uppercase;letter-spacing:.5px}
table{width:100%;border-collapse:collapse;margin-bottom:16px}
thead tr{background:#0E2A47}
thead th{color:#FFF;padding:6px 6px;font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;text-align:left}
thead th.r{text-align:right}
tbody td{padding:5px 6px;font-size:9px;border-bottom:1px solid #EFF2F7}
tbody td.r{text-align:right}
tr.alt{background:#F7F8FB}
tfoot td{background:#0E2A47;color:#FFF;font-weight:700;padding:6px 6px;font-size:9px}
tfoot td.r{text-align:right}
.footer{margin-top:24px;text-align:center;font-size:9px;color:#A8B0BF;border-top:1px solid #EFF2F7;padding-top:10px}
</style></head><body>
<div class="ph">
  <div class="ph-right">
    <div class="badge">COULAGE</div><br/>
    <strong>${data.marketeur_nom}</strong>
  </div>
  <div class="ph-title">COULAGE DES MARKETEURS</div>
  <div class="ph-sub">Système de Gestion des Dépôts Pétroliers</div>
  ${periodeNom ? `<div class="ph-sub" style="margin-top:8px">${periodeNom}</div>` : ''}
</div>
<div class="kpi">
  <div class="k" style="background:#EDE9FE">
    <div class="k-lbl">Volume sorti total</div>
    <div class="k-val" style="color:#6E47C7">${fmtN(data.total_volume_sorti)} L</div>
  </div>
  <div class="k" style="background:#FEF3C7">
    <div class="k-lbl">Montant total</div>
    <div class="k-val" style="color:#E67A2A">${fmtN(data.total_montant)} FCFA</div>
  </div>
</div>
${sections}
<div class="footer">Généré le ${new Date().toLocaleDateString('fr-FR')} · SGDS Mobile v2.0 · ${data.marketeur_nom}</div>
</body></html>`;
}

// ── Composant principal ───────────────────────────────────────────

export function CoulageScreen() {
  const navigation = useNavigation();

  const [data,        setData]        = useState<CoulageResponse | null>(null);
  const [periodes,    setPeriodes]    = useState<Periode[]>([]);
  const [selectedPer, setSelectedPer] = useState<Periode | null>(null);
  const multiDepot = plusieursDepots(periodes);
  const [loading,     setLoading]     = useState(true);
  const [refreshing,  setRefreshing]  = useState(false);
  const [error,       setError]       = useState<string | null>(null);
  const [exporting,   setExporting]   = useState(false);
  const [showModal,   setShowModal]   = useState(false);

  useEffect(() => {
    etatsApi.periodes().then(r => setPeriodes(r.data)).catch(() => {});
  }, []);

  const load = useCallback(async (periodeId?: number, isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError(null);
    try {
      const r = await etatsApi.coulage(periodeId);
      setData(r.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e?.message ?? 'Impossible de charger les données.');
      setData(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(selectedPer?.id); }, [load, selectedPer]));

  const exportPdf = async () => {
    if (!data) return;
    setExporting(true);
    try {
      const html = buildHtml(data, selectedPer ? libellePeriode(selectedPer, multiDepot) : undefined);
      const { uri } = await Print.printToFileAsync({ html });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, { mimeType: 'application/pdf', dialogTitle: 'Coulage' });
      } else {
        await Print.printAsync({ html });
      }
    } catch (e) { console.warn(e); }
    finally { setExporting(false); }
  };

  // Grouper les lignes par période pour l'affichage
  const periodeGroups: { nom: string; lignes: CoulageLigne[] }[] = [];
  if (data) {
    const map: Record<string, CoulageLigne[]> = {};
    data.lignes.forEach(l => {
      const cle = l.periode_depot ? `${l.periode_nom} — ${l.periode_depot}` : l.periode_nom;
      if (!map[cle]) map[cle] = [];
      map[cle].push(l);
    });
    Object.entries(map).forEach(([nom, lignes]) => periodeGroups.push({ nom, lignes }));
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <LinearGradient
        colors={['#5B21B6', '#4C1D95', '#3B0764']}
        style={styles.hero}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
      >
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color={Colors.white} />
        </TouchableOpacity>
        <View style={styles.heroContent}>
          <Text style={styles.heroSub}>Analyse</Text>
          <Text style={styles.heroTitle}>Coulage des Marketeurs</Text>
          {data && data.lignes.length > 0 && (
            <Text style={styles.heroSub2}>{data.lignes.length} ligne(s)</Text>
          )}
        </View>
        <TouchableOpacity style={styles.pdfBtn} onPress={exportPdf} disabled={exporting || !data}>
          {exporting
            ? <ActivityIndicator size="small" color={Colors.white} />
            : <Ionicons name="share-outline" size={20} color={Colors.white} />}
        </TouchableOpacity>
      </LinearGradient>

      {/* Filtre période */}
      <View style={styles.filterRow}>
        <TouchableOpacity style={styles.perBtn} onPress={() => setShowModal(true)}>
          <Ionicons name="calendar-outline" size={14} color="#5B21B6" />
          <Text style={styles.perBtnText}>{selectedPer ? libellePeriode(selectedPer, multiDepot) : 'Toutes les périodes'}</Text>
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
          <ActivityIndicator size="large" color="#5B21B6" />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Ionicons name="alert-circle-outline" size={48} color={Colors.red} />
          <Text style={[styles.emptyText, { color: Colors.red }]}>Erreur de chargement</Text>
          <Text style={styles.errorSub}>{error}</Text>
          <TouchableOpacity onPress={() => load(selectedPer?.id)} style={styles.retryBtn}>
            <Text style={styles.retryBtnText}>Réessayer</Text>
          </TouchableOpacity>
        </View>
      ) : !data || data.lignes.length === 0 ? (
        <View style={styles.center}>
          <Ionicons name="analytics-outline" size={48} color={Colors.silver} />
          <Text style={styles.emptyText}>Aucune clôture de coulage disponible</Text>
          <Text style={styles.emptySubText}>
            Les données de coulage apparaissent après la clôture mensuelle.
          </Text>
        </View>
      ) : (
        <ScrollView style={styles.scroll} contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => load(selectedPer?.id, true)}
              colors={['#5B21B6']}
            />
          }>

          {/* KPI totaux */}
          <View style={styles.kpiRow}>
            <View style={[styles.kpiCard, { backgroundColor: '#EDE9FE' }]}>
              <Ionicons name="water-outline" size={18} color="#5B21B6" />
              <Text style={styles.kpiLabel}>Volume sorti total</Text>
              <Text style={[styles.kpiValue, { color: '#5B21B6' }]}>
                {fmtN(data.total_volume_sorti)}
              </Text>
              <Text style={styles.kpiUnit}>litres</Text>
            </View>
            <View style={[styles.kpiCard, { backgroundColor: '#FEF3C7' }]}>
              <Ionicons name="cash-outline" size={18} color="#92400E" />
              <Text style={styles.kpiLabel}>Montant total</Text>
              <Text style={[styles.kpiValue, { color: '#92400E' }]}>
                {fmtN(data.total_montant)}
              </Text>
              <Text style={styles.kpiUnit}>FCFA</Text>
            </View>
          </View>

          {/* Groupes par période */}
          {periodeGroups.map(group => (
            <PeriodeGroup key={group.nom} group={group} />
          ))}
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
            <TouchableOpacity
              style={styles.perItem}
              onPress={() => { setSelectedPer(null); setShowModal(false); }}
            >
              <Text style={styles.perItemText}>Toutes les périodes</Text>
            </TouchableOpacity>
            <FlatList
              data={periodes}
              keyExtractor={p => String(p.id)}
              renderItem={({ item: p }) => (
                <TouchableOpacity
                  style={[styles.perItem, selectedPer?.id === p.id && styles.perItemActive]}
                  onPress={() => { setSelectedPer(p); setShowModal(false); }}
                >
                  <Text style={[styles.perItemText, selectedPer?.id === p.id && { color: Colors.white }]}>
                    {libellePeriode(p, multiDepot)}
                  </Text>
                  {p.statut === 'CLOTUREE' && (
                    <View style={styles.clotureBadge}>
                      <Text style={styles.clotureBadgeText}>CLÔTURÉE</Text>
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

// ── PeriodeGroup ──────────────────────────────────────────────────

function PeriodeGroup({ group }: { group: { nom: string; lignes: CoulageLigne[] } }) {
  const totMontant = group.lignes.reduce((s, l) => s + Number(l.montant), 0);
  const totVolume  = group.lignes.reduce((s, l) => s + Number(l.volume_sorti), 0);

  return (
    <View style={styles.groupContainer}>
      {/* En-tête période */}
      <View style={styles.groupHeader}>
        <View style={styles.groupHeaderLeft}>
          <Ionicons name="calendar" size={14} color="#5B21B6" />
          <Text style={styles.groupTitle}>{group.nom}</Text>
          <Text style={styles.groupCount}>{group.lignes.length} produit(s)</Text>
        </View>
        <View style={styles.groupSummary}>
          <Text style={styles.groupVol}>{fmtN(totVolume)} L</Text>
          <Text style={styles.groupMontant}>{fmtN(totMontant)} FCFA</Text>
        </View>
      </View>

      {/* Lignes produits */}
      {group.lignes.map((l, i) => (
        <CoulageLigneCard key={`${l.produit_id}-${i}`} ligne={l} index={i} />
      ))}
    </View>
  );
}

// ── CoulageLigneCard ──────────────────────────────────────────────

function CoulageLigneCard({ ligne: l, index }: { ligne: CoulageLigne; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <TouchableOpacity
      style={[styles.ligneCard, index % 2 === 1 && { backgroundColor: '#FAFAFF' }]}
      onPress={() => setExpanded(e => !e)}
      activeOpacity={0.8}
    >
      {/* Ligne principale */}
      <View style={styles.ligneTop}>
        <View style={styles.ligneLeft}>
          <View style={styles.sigleBadge}>
            <Text style={styles.sigleText}>{l.produit_sigle}</Text>
          </View>
          <Text style={styles.ligneNom}>{l.produit_nom}</Text>
        </View>
        <View style={styles.ligneRight}>
          <Text style={styles.ligneMontant}>{fmtN(l.montant)} FCFA</Text>
          <Text style={styles.ligneVol}>{fmtN(l.volume_sorti)} L sorti</Text>
        </View>
        <Ionicons
          name={expanded ? 'chevron-up' : 'chevron-down'}
          size={14} color={Colors.slate} style={{ marginLeft: 8 }}
        />
      </View>

      {/* Détail expandable */}
      {expanded && (
        <View style={styles.ligneDetail}>
          <View style={styles.detailDivider} />
          <StatRow label="Brut entrée"   value={fmtN(l.brut_entree)   + ' L'} />
          <StatRow label="Coulage entrée" value={fmtN(l.coul_entree)  + ' L'} valueColor="#D63B3B" />
          <StatRow label="Entrée nette"  value={fmtN(l.entree_nette)  + ' L'} valueColor={Colors.entree} />
          <StatRow label="Sortie"        value={fmtN(l.sortie)        + ' L'} />
          <StatRow label="QP Coulage"    value={fmtN(l.qp_coul)       + ' L'} />
          <StatRow label="Volume sorti"  value={fmtN(l.volume_sorti)  + ' L'} valueColor="#5B21B6" />
          <StatRow label="Prix unitaire" value={fmtN(l.prix_unitaire, 4) + ' FCFA/L'} />
          <StatRow label="Montant"       value={fmtN(l.montant)       + ' FCFA'} valueColor="#92400E" bold />
          {l.motif ? <StatRow label="Motif" value={l.motif} /> : null}
        </View>
      )}
    </TouchableOpacity>
  );
}

function StatRow({ label, value, valueColor, bold }: {
  label: string; value: string; valueColor?: string; bold?: boolean;
}) {
  return (
    <View style={styles.statRow}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={[styles.statValue, valueColor ? { color: valueColor } : {}, bold ? { fontWeight: '800' } : {}]}>
        {value}
      </Text>
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
  backBtn:     { marginRight: 10, padding: 4 },
  heroContent: { flex: 1 },
  heroSub:     { color: Colors.white + 'bf', fontSize: 10, fontWeight: '600', letterSpacing: 0.5 },
  heroSub2:    { color: Colors.white + 'b3', fontSize: 11, marginTop: 2 },
  heroTitle:   { color: Colors.white, fontSize: 18, fontWeight: '800', letterSpacing: -0.3 },
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
    flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: '#EDE9FE', borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 8,
  },
  perBtnText: { flex: 1, fontSize: 13, fontWeight: '600', color: '#5B21B6' },
  clearBtn:   { padding: 4 },

  scroll:        { flex: 1 },
  content:       { padding: 16, paddingBottom: 40 },
  center:        { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10, padding: 24 },
  emptyText:     { fontSize: 15, color: Colors.slate, textAlign: 'center', fontWeight: '600' },
  emptySubText:  { fontSize: 12, color: Colors.silver, textAlign: 'center', lineHeight: 18 },

  kpiRow:  { flexDirection: 'row', gap: 10, marginBottom: 16 },
  kpiCard: {
    flex: 1, borderRadius: 14, padding: 12, alignItems: 'center', gap: 4,
    borderWidth: 1, borderColor: Colors.cloud,
  },
  kpiLabel: { fontSize: 10, fontWeight: '600', color: Colors.slate, textTransform: 'uppercase', letterSpacing: 0.3 },
  kpiValue: { fontSize: 18, fontWeight: '800' },
  kpiUnit:  { fontSize: 10, color: Colors.slate },

  groupContainer: {
    marginBottom: 14,
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1, borderColor: Colors.cloud,
    backgroundColor: Colors.white,
    shadowColor: Colors.ink, shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05, shadowRadius: 6, elevation: 2,
  },
  groupHeader: {
    backgroundColor: '#EDE9FE',
    paddingHorizontal: 12, paddingVertical: 10,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
  },
  groupHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  groupTitle:  { fontSize: 13, fontWeight: '800', color: '#3B0764' },
  groupCount:  { fontSize: 11, color: '#5B21B6', fontWeight: '500' },
  groupSummary: { alignItems: 'flex-end' },
  groupVol:     { fontSize: 11, fontWeight: '700', color: '#5B21B6' },
  groupMontant: { fontSize: 12, fontWeight: '800', color: '#92400E' },

  ligneCard: {
    paddingHorizontal: 12, paddingVertical: 10,
    backgroundColor: Colors.white,
    borderTopWidth: 1, borderTopColor: Colors.cloud,
  },
  ligneTop:  { flexDirection: 'row', alignItems: 'center' },
  ligneLeft: { flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 },
  sigleBadge: { backgroundColor: Colors.navy, borderRadius: 5, paddingHorizontal: 6, paddingVertical: 2 },
  sigleText:  { color: Colors.white, fontSize: 8, fontWeight: '700' },
  ligneNom:   { fontSize: 12, fontWeight: '700', color: Colors.ink, flex: 1 },
  ligneRight: { alignItems: 'flex-end' },
  ligneMontant: { fontSize: 13, fontWeight: '800', color: '#92400E' },
  ligneVol:     { fontSize: 10, color: '#5B21B6', fontWeight: '600' },

  ligneDetail:  { marginTop: 8 },
  detailDivider: { height: 1, backgroundColor: Colors.cloud, marginBottom: 8 },
  statRow:   { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 3 },
  statLabel: { fontSize: 11, color: Colors.slate },
  statValue: { fontSize: 12, fontWeight: '600', color: Colors.ink },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalBox: {
    backgroundColor: Colors.white, borderTopLeftRadius: 20, borderTopRightRadius: 20,
    maxHeight: '70%', paddingBottom: 24,
  },
  modalHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    padding: 16, borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  modalTitle:  { fontSize: 16, fontWeight: '800', color: Colors.ink },
  perItem: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud, gap: 10,
  },
  perItemActive: { backgroundColor: '#5B21B6' },
  perItemText:   { flex: 1, fontSize: 14, fontWeight: '600', color: Colors.ink },
  clotureBadge:  { backgroundColor: Colors.cloud, borderRadius: 5, paddingHorizontal: 6, paddingVertical: 2 },
  clotureBadgeText: { fontSize: 9, fontWeight: '700', color: Colors.slate },

  retryBtn: {
    marginTop: 12,
    backgroundColor: '#5B21B6',
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  retryBtnText: { color: Colors.white, fontWeight: '700', fontSize: 13 },
  errorSub: { fontSize: 12, color: Colors.slate, textAlign: 'center', marginTop: 4, maxWidth: 260 },
});
