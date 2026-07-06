import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator,
  RefreshControl, Modal, FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Print   from 'expo-print';
import * as Sharing from 'expo-sharing';
import { useNavigation, useFocusEffect } from '@react-navigation/native';

import { Colors }   from '../../constants/colors';
import { etatsApi } from '../../api/etats';
import type { FraisPassageResponse, FraisPassageProduit, Periode } from '../../api/etats';
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

function fmtDate(d: string): string {
  if (!d || d.length < 10) return '—';
  return d.slice(8, 10) + '/' + d.slice(5, 7) + '/' + d.slice(0, 4);
}

// ── PDF ───────────────────────────────────────────────────────────

function buildHtml(data: FraisPassageResponse): string {
  const rows = data.produits.map((p, i) => `
    <tr${i % 2 === 1 ? ' class="alt"' : ''}>
      <td>
        <span style="background:#0E2A47;color:#FFF;padding:1px 6px;border-radius:4px;font-weight:700;font-size:9px">
          ${p.produit_sigle}
        </span>
        &nbsp;${p.produit_nom}
      </td>
      <td class="r" style="font-weight:800;color:#E67A2A">${fmtN(p.prix_passage, 4)}</td>
      <td class="r">
        ${p.is_global
          ? '<span style="background:#EFF2F7;color:#6B7589;padding:2px 6px;border-radius:4px;font-size:9px">GLOBAL</span>'
          : '<span style="background:#D8F3E2;color:#1F9D55;padding:2px 6px;border-radius:4px;font-size:9px">SPÉCIFIQUE</span>'}
      </td>
    </tr>`).join('');

  return `<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;font-size:10px;color:#0B1220;padding:20px 24px}
.ph{background:#0E2A47;color:#FFF;border-radius:10px;padding:16px 20px;margin-bottom:18px;position:relative;overflow:hidden}
.ph::after{content:'';position:absolute;right:-40px;top:-40px;width:160px;height:160px;border-radius:50%;background:rgba(230,122,42,.18)}
.ph-title{font-size:18px;font-weight:800}
.ph-sub{font-size:11px;opacity:.75;margin-top:2px}
.badge{display:inline-block;background:#E67A2A;color:#FFF;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:800;margin-bottom:4px}
.ph-right{float:right;text-align:right}
.info-box{background:#E8EEF6;border-radius:8px;padding:12px 16px;margin-bottom:18px;display:flex;align-items:center;gap:10px}
.info-label{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6B7589}
.info-val{font-size:18px;font-weight:800;color:#E67A2A}
.sec{font-size:11px;font-weight:800;color:#0E2A47;margin:18px 0 6px;padding-bottom:4px;border-bottom:2px solid #0E2A47;text-transform:uppercase;letter-spacing:.5px}
table{width:100%;border-collapse:collapse}
thead tr{background:#0E2A47}
thead th{color:#FFF;padding:7px 8px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;text-align:left}
thead th.r{text-align:right}
tbody td{padding:6px 8px;font-size:10px;border-bottom:1px solid #EFF2F7}
tbody td.r{text-align:right}
tr.alt{background:#F7F8FB}
.footer{margin-top:24px;text-align:center;font-size:9px;color:#A8B0BF;border-top:1px solid #EFF2F7;padding-top:10px}
</style></head><body>
<div class="ph">
  <div class="ph-right">
    <div class="badge">FRAIS PASSAGE</div>
  </div>
  <div class="ph-title">FRAIS DE PASSAGE</div>
  <div class="ph-sub">Système de Gestion des Dépôts Pétroliers</div>
  <div class="ph-sub" style="margin-top:8px">En vigueur depuis le ${fmtDate(data.date_application)}</div>
</div>
<table style="margin-bottom:16px">
  <thead><tr><th>Tarif global en vigueur</th><th class="r">Valeur</th></tr></thead>
  <tbody><tr>
    <td>Prix unitaire de passage</td>
    <td class="r" style="font-weight:800;color:#E67A2A;font-size:14px">${fmtN(data.tarif_global, 4)} FCFA/L</td>
  </tr></tbody>
</table>
<div class="sec">Tarifs par produit</div>
<table>
  <thead><tr>
    <th>Produit</th>
    <th class="r">Prix (FCFA/L)</th>
    <th class="r">Type</th>
  </tr></thead>
  <tbody>${rows}</tbody>
</table>
<div class="footer">Généré le ${new Date().toLocaleDateString('fr-FR')} · SGDS Mobile v2.0</div>
</body></html>`;
}

// ── Composant ─────────────────────────────────────────────────────

export function FraisPassageScreen() {
  const navigation = useNavigation();

  const [data,       setData]       = useState<FraisPassageResponse | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error,      setError]      = useState<string | null>(null);
  const [exporting,  setExporting]  = useState(false);
  const [periodes,    setPeriodes]    = useState<Periode[]>([]);
  const [selectedPer, setSelectedPer] = useState<Periode | null>(null);
  const multiDepot = plusieursDepots(periodes);
  const [showModal,   setShowModal]   = useState(false);

  useEffect(() => {
    etatsApi.periodes().then(r => setPeriodes(r.data)).catch(() => {});
  }, []);

  const load = useCallback(async (periodeId?: number, isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError(null);
    try {
      const r = await etatsApi.fraisPassage(periodeId);
      setData(r.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e?.message ?? 'Impossible de charger les frais de passage.');
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
      const html = buildHtml(data);
      const { uri } = await Print.printToFileAsync({ html });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, { mimeType: 'application/pdf', dialogTitle: 'Frais de Passage' });
      } else {
        await Print.printAsync({ html });
      }
    } catch (e) {
      console.warn('PDF error', e);
    } finally {
      setExporting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <LinearGradient
        colors={['#B45309', '#92400E', '#78350F']}
        style={styles.hero}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
      >
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color={Colors.white} />
        </TouchableOpacity>
        <View style={styles.heroContent}>
          <Text style={styles.heroSub}>Tarification</Text>
          <Text style={styles.heroTitle}>Frais de Passage</Text>
          {data && (
            <Text style={styles.heroSub2}>
              En vigueur depuis le {fmtDate(data.date_application)}
            </Text>
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
          <Ionicons name="calendar-outline" size={14} color="#92400E" />
          <Text style={styles.perBtnText}>
            {selectedPer ? libellePeriode(selectedPer, multiDepot) : "Tarif en vigueur aujourd'hui"}
          </Text>
          <Ionicons name="chevron-down" size={14} color={Colors.slate} />
        </TouchableOpacity>
        {selectedPer && (
          <TouchableOpacity onPress={() => setSelectedPer(null)} style={styles.clearBtn}>
            <Ionicons name="close-circle" size={18} color={Colors.slate} />
          </TouchableOpacity>
        )}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#92400E" />
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
      ) : !data ? (
        <View style={styles.center}>
          <Ionicons name="cash-outline" size={48} color={Colors.silver} />
          <Text style={styles.emptyText}>Aucun tarif configuré</Text>
        </View>
      ) : (
        <ScrollView style={styles.scroll} contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => load(selectedPer?.id, true)}
              colors={[Colors.navy]}
            />
          }>

          {/* Tarif global */}
          <View style={styles.globalCard}>
            <View style={styles.globalLeft}>
              <View style={styles.globalIconBox}>
                <Ionicons name="pricetag" size={22} color="#92400E" />
              </View>
              <View>
                <Text style={styles.globalLabel}>Tarif Global en Vigueur</Text>
                <Text style={styles.globalDate}>
                  {data.date_application ? `Depuis le ${fmtDate(data.date_application)}` : 'Tarif par défaut (aucun paramétrage)'}
                </Text>
              </View>
            </View>
            <View style={styles.globalRight}>
              <Text style={styles.globalValue}>{fmtN(data.tarif_global, 4)}</Text>
              <Text style={styles.globalUnit}>FCFA / litre</Text>
            </View>
          </View>

          {/* Info */}
          <View style={styles.infoBanner}>
            <Ionicons name="information-circle-outline" size={16} color={Colors.navy} />
            <Text style={styles.infoText}>
              Le prix de passage peut être spécifique à chaque produit. Si aucun tarif spécifique
              n'est défini, le tarif global s'applique.
            </Text>
          </View>

          {/* Liste des produits */}
          <Text style={styles.sectionTitle}>TARIFS PAR PRODUIT</Text>
          {data.produits.map((p, i) => (
            <ProduitCard key={p.produit_id} produit={p} index={i} />
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
              <Text style={styles.perItemText}>Tarif en vigueur aujourd'hui</Text>
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

// ── ProduitCard ───────────────────────────────────────────────────

function ProduitCard({ produit: p, index }: { produit: FraisPassageProduit; index: number }) {
  const bg = index % 2 === 1 ? '#FDF8F0' : Colors.white;
  return (
    <View style={[styles.prodCard, { backgroundColor: bg }]}>
      <View style={styles.prodLeft}>
        <View style={styles.sigleBadge}>
          <Text style={styles.sigleText}>{p.produit_sigle}</Text>
        </View>
        <View>
          <Text style={styles.prodNom}>{p.produit_nom}</Text>
          <View style={[styles.typeBadge, p.is_global ? styles.typeBadgeGlobal : styles.typeBadgeSpec]}>
            <Text style={[styles.typeText, p.is_global ? styles.typeTextGlobal : styles.typeTextSpec]}>
              {p.is_global ? 'TARIF GLOBAL' : 'TARIF SPÉCIFIQUE'}
            </Text>
          </View>
        </View>
      </View>
      <View style={styles.prodRight}>
        <Text style={styles.prodPrix}>{fmtN(p.prix_passage, 4)}</Text>
        <Text style={styles.prodUnit}>FCFA/L</Text>
      </View>
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
    backgroundColor: '#FEF3C7', borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 8,
  },
  perBtnText: { flex: 1, fontSize: 13, fontWeight: '600', color: '#92400E' },
  clearBtn:   { padding: 4 },

  scroll:    { flex: 1 },
  content:   { padding: 16, paddingBottom: 40 },
  center:    { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  emptyText: { fontSize: 14, color: Colors.slate, textAlign: 'center' },

  // Modal sélection période
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
  perItemActive: { backgroundColor: '#92400E' },
  perItemText:   { flex: 1, fontSize: 14, fontWeight: '600', color: Colors.ink },
  clotureBadge:  { backgroundColor: Colors.cloud, borderRadius: 5, paddingHorizontal: 6, paddingVertical: 2 },
  clotureBadgeText: { fontSize: 9, fontWeight: '700', color: Colors.slate },

  globalCard: {
    backgroundColor: Colors.white,
    borderRadius: 16, padding: 16, marginBottom: 12,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    borderWidth: 1, borderColor: '#FDE68A',
    shadowColor: '#92400E', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08, shadowRadius: 6, elevation: 2,
  },
  globalLeft: { flexDirection: 'row', alignItems: 'center', gap: 12, flex: 1 },
  globalIconBox: {
    width: 46, height: 46, borderRadius: 13,
    backgroundColor: '#FEF3C7',
    alignItems: 'center', justifyContent: 'center',
  },
  globalLabel: { fontSize: 13, fontWeight: '700', color: Colors.ink },
  globalDate:  { fontSize: 11, color: Colors.slate, marginTop: 2 },
  globalRight: { alignItems: 'flex-end' },
  globalValue: { fontSize: 22, fontWeight: '800', color: '#92400E' },
  globalUnit:  { fontSize: 10, color: Colors.slate },

  infoBanner: {
    backgroundColor: Colors.navyTint,
    borderRadius: 12, padding: 12,
    flexDirection: 'row', alignItems: 'flex-start', gap: 8,
    marginBottom: 16,
    borderWidth: 1, borderColor: Colors.navy + '20',
  },
  infoText: { flex: 1, fontSize: 11, color: Colors.navy, lineHeight: 17 },

  sectionTitle: {
    fontSize: 10, fontWeight: '800', color: Colors.slate,
    textTransform: 'uppercase', letterSpacing: 0.5,
    marginBottom: 8,
  },

  prodCard: {
    borderRadius: 12, padding: 14,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    marginBottom: 6,
    borderWidth: 1, borderColor: Colors.cloud,
  },
  prodLeft:    { flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 },
  sigleBadge:  { backgroundColor: Colors.navy, borderRadius: 6, paddingHorizontal: 7, paddingVertical: 3 },
  sigleText:   { color: Colors.white, fontSize: 9, fontWeight: '700' },
  prodNom:     { fontSize: 13, fontWeight: '700', color: Colors.ink, marginBottom: 3 },
  typeBadge:   { borderRadius: 5, paddingHorizontal: 6, paddingVertical: 2, alignSelf: 'flex-start' },
  typeBadgeGlobal: { backgroundColor: Colors.cloud },
  typeBadgeSpec:   { backgroundColor: Colors.greenSoft },
  typeText:     { fontSize: 9, fontWeight: '700', letterSpacing: 0.3 },
  typeTextGlobal: { color: Colors.slate },
  typeTextSpec:   { color: Colors.entree },
  prodRight:   { alignItems: 'flex-end' },
  prodPrix:    { fontSize: 16, fontWeight: '800', color: '#92400E' },
  prodUnit:    { fontSize: 10, color: Colors.slate },

  retryBtn: {
    marginTop: 12,
    backgroundColor: Colors.navy,
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  retryBtnText: { color: Colors.white, fontWeight: '700', fontSize: 13 },
  errorSub: { fontSize: 12, color: Colors.slate, textAlign: 'center', marginTop: 4, maxWidth: 260 },
});
