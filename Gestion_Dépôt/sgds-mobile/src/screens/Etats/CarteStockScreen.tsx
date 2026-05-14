import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Modal, FlatList, ActivityIndicator, Alert, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import dayjs from 'dayjs';

import { etatsApi, StockGlobalResponse, Produit, StockGlobalFilters } from '../../api/etats';
import { Colors, FontSize, Radius } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';
import { buildCarteStockHtml } from '../../utils/pdfTemplate';

// ── Constantes ────────────────────────────────────────────────────

const PERIODS = [
  { label: '7j',   days: 7 },
  { label: '30j',  days: 30 },
  { label: '3m',   days: 90 },
  { label: '12m',  days: 365 },
  { label: 'Tout', days: null },
];

const TYPE_COLORS: Record<string, string> = {
  ENTREE:       Colors.entree,
  SORTIE:       Colors.sortie,
  CESSION:      Colors.cession,
  ACQUITTEMENT: Colors.acquittement,
};

const TYPE_LABELS: Record<string, string> = {
  ENTREE: 'Entrée', SORTIE: 'Sortie',
  CESSION: 'Cession', ACQUITTEMENT: 'Acquitt.',
};

function fmtN(n: any, dec = 0): string {
  const v = Number(n);
  if (isNaN(v)) return '0';
  return v.toLocaleString('fr-FR', { maximumFractionDigits: dec });
}

function fmtDate(d: string): string {
  if (!d || d.length < 10) return '—';
  return d.slice(8, 10) + '/' + d.slice(5, 7);
}

// ── Composant ─────────────────────────────────────────────────────

export function CarteStockScreen() {
  const navigation = useNavigation();

  const [produits, setProduits]             = useState<Produit[]>([]);
  const [selectedProduit, setSelectedProduit] = useState<Produit | null>(null);
  const [period, setPeriod]                 = useState('30j');
  const [data, setData]                     = useState<StockGlobalResponse | null>(null);
  const [loading, setLoading]               = useState(true);
  const [refreshing, setRefreshing]         = useState(false);
  const [error, setError]                   = useState<string | null>(null);
  const [showProduitModal, setShowProduitModal] = useState(false);
  const [generatingPdf, setGeneratingPdf]   = useState(false);

  // Charger la liste des produits une seule fois
  useEffect(() => {
    etatsApi.produits()
      .then(res => setProduits(res.data))
      .catch(() => {});
  }, []);

  const buildFilters = useCallback((): StockGlobalFilters => {
    const filters: StockGlobalFilters = {};
    if (selectedProduit) filters.produit = selectedProduit.id;
    const p = PERIODS.find(x => x.label === period);
    if (p?.days) {
      filters.date_debut = dayjs().subtract(p.days, 'day').format('YYYY-MM-DD');
      filters.date_fin   = dayjs().format('YYYY-MM-DD');
    }
    return filters;
  }, [selectedProduit, period]);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError(null);
    try {
      const res = await etatsApi.stockGlobal(buildFilters());
      setData(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [buildFilters]);

  useFocusEffect(useCallback(() => { fetchData(); }, [fetchData]));

  // ── Génération PDF ───────────────────────────────────────────────

  const generatePdf = async () => {
    if (!data) return;
    setGeneratingPdf(true);
    try {
      const p = PERIODS.find(x => x.label === period);
      const periodeLabel = p?.days
        ? `Derniers ${period} — du ${dayjs().subtract(p.days, 'day').format('DD/MM/YYYY')} au ${dayjs().format('DD/MM/YYYY')}`
        : 'Tous les mouvements';

      const html = buildCarteStockHtml({
        marketeurNom:          data.marketeur_nom || 'Marketeur',
        produitNom:            data.produit_nom   || selectedProduit?.nom || 'Tous les produits',
        produitSigle:          data.produit_sigle || selectedProduit?.sigle || 'ALL',
        periodeLabel,
        lignes:                data.lignes,
        cumul_entrees_ambiant: Number(data.cumul_entrees_ambiant),
        cumul_sorties_ambiant: Number(data.cumul_sorties_ambiant),
        stock_final_ambiant:   Number(data.stock_final_ambiant),
        stock_final_15:        Number(data.stock_final_15),
        generatedAt:           dayjs().format('DD/MM/YYYY HH:mm'),
      });

      const { uri } = await Print.printToFileAsync({ html, base64: false });
      const canShare = await Sharing.isAvailableAsync();

      if (canShare) {
        await Sharing.shareAsync(uri, {
          mimeType: 'application/pdf',
          dialogTitle: 'Carte de Stock — SGDS',
          UTI: 'com.adobe.pdf',
        });
      } else {
        await Print.printAsync({ html });
      }
    } catch (err) {
      Alert.alert('Erreur PDF', 'Impossible de générer le document.');
    } finally {
      setGeneratingPdf(false);
    }
  };

  // ── Rendu ────────────────────────────────────────────────────────

  if (loading) return <LoadingSpinner fullScreen message="Chargement de la carte de stock..." />;
  if (error)   return <ErrorMessage message={error} onRetry={() => fetchData()} />;

  const lignes  = data?.lignes            ?? [];
  const entrees = Number(data?.cumul_entrees_ambiant ?? 0);
  const sorties = Number(data?.cumul_sorties_ambiant ?? 0);
  const stock   = Number(data?.stock_final_ambiant   ?? 0);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* ── Barre de navigation ─────────────────────────────────── */}
      <View style={styles.navbar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color={Colors.ink} />
        </TouchableOpacity>
        <View style={styles.navCenter}>
          <Text style={styles.navTitle}>Carte de Stock</Text>
          {data?.marketeur_nom && (
            <Text style={styles.navSub}>{data.marketeur_nom}</Text>
          )}
        </View>
        <TouchableOpacity
          style={[styles.pdfBtn, generatingPdf && styles.pdfBtnDisabled]}
          onPress={generatePdf}
          disabled={generatingPdf}
        >
          {generatingPdf
            ? <ActivityIndicator size="small" color={Colors.white} />
            : <Ionicons name="document-text-outline" size={16} color={Colors.white} />
          }
          <Text style={styles.pdfBtnText}>{generatingPdf ? '…' : 'PDF'}</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchData(true)}
            colors={[Colors.navy]}
          />
        }
      >
        {/* ── Filtres ──────────────────────────────────────────── */}
        <View style={styles.filtersBar}>
          {/* Sélecteur produit */}
          <TouchableOpacity
            style={styles.produitBtn}
            onPress={() => setShowProduitModal(true)}
          >
            <Ionicons name="water-outline" size={14} color={Colors.navy} />
            <Text style={styles.produitBtnText} numberOfLines={1}>
              {selectedProduit?.nom ?? 'Tous les produits'}
            </Text>
            <Ionicons name="chevron-down" size={12} color={Colors.slate} />
          </TouchableOpacity>

          {/* Période */}
          <View style={styles.segmented}>
            {PERIODS.map(p => (
              <TouchableOpacity
                key={p.label}
                onPress={() => setPeriod(p.label)}
                style={[styles.segBtn, period === p.label && styles.segBtnActive]}
                activeOpacity={0.8}
              >
                <Text style={[styles.segText, period === p.label && styles.segTextActive]}>
                  {p.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* ── KPI Stock ────────────────────────────────────────── */}
        <View style={styles.kpiRow}>
          <View style={[styles.kpi, styles.kpiMain]}>
            <Text style={styles.kpiLabel}>Stock final</Text>
            <Text style={styles.kpiValue}>{fmtN(stock)}</Text>
            <Text style={styles.kpiUnit}>L ambiant</Text>
          </View>
          <View style={styles.kpiRight}>
            <View style={[styles.kpiSmall, { borderColor: Colors.entree + '30' }]}>
              <Ionicons name="arrow-down" size={11} color={Colors.entree} />
              <Text style={[styles.kpiSmallVal, { color: Colors.entree }]}>{fmtN(entrees)} L</Text>
              <Text style={styles.kpiSmallLbl}>Entrées</Text>
            </View>
            <View style={[styles.kpiSmall, { borderColor: Colors.sortie + '30' }]}>
              <Ionicons name="arrow-up" size={11} color={Colors.sortie} />
              <Text style={[styles.kpiSmallVal, { color: Colors.sortie }]}>{fmtN(sorties)} L</Text>
              <Text style={styles.kpiSmallLbl}>Sorties</Text>
            </View>
          </View>
        </View>

        {/* ── Tableau mouvements ───────────────────────────────── */}
        <View style={styles.tableWrap}>
          <View style={styles.tableHeader}>
            <Text style={styles.tableTitle}>Mouvements détaillés</Text>
            <View style={styles.countChip}>
              <Text style={styles.countText}>{lignes.length}</Text>
            </View>
          </View>

          {/* Entête colonnes */}
          <View style={styles.colHead}>
            <Text style={[styles.th, { width: 44 }]}>Date</Text>
            <Text style={[styles.th, { flex: 1 }]}>Réf. / Type</Text>
            <Text style={[styles.th, { width: 72, textAlign: 'right' }]}>Entrée L</Text>
            <Text style={[styles.th, { width: 72, textAlign: 'right' }]}>Sortie L</Text>
            <Text style={[styles.th, { width: 72, textAlign: 'right' }]}>Stock L</Text>
          </View>

          {lignes.length === 0 ? (
            <View style={styles.empty}>
              <Ionicons name="document-outline" size={36} color={Colors.silver} />
              <Text style={styles.emptyText}>Aucun mouvement sur cette période</Text>
            </View>
          ) : (
            lignes.map((l, i) => {
              const color   = TYPE_COLORS[l.type] ?? Colors.slate;
              const hasIn   = Number(l.entree_ambiant) > 0;
              const hasOut  = Number(l.sortie_ambiant) > 0;
              return (
                <View key={i} style={[styles.row, i % 2 === 1 && styles.rowAlt]}>
                  <Text style={[styles.tdDate, { width: 44 }]}>{fmtDate(l.date)}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.tdRef} numberOfLines={1}>
                      {l.reference || '—'}
                    </Text>
                    <Text style={[styles.tdType, { color }]}>
                      {TYPE_LABELS[l.type] ?? l.type}
                    </Text>
                  </View>
                  <Text style={[styles.tdQte, { width: 72, color: hasIn ? Colors.entree : Colors.silver }]}>
                    {hasIn ? fmtN(l.entree_ambiant) : '—'}
                  </Text>
                  <Text style={[styles.tdQte, { width: 72, color: hasOut ? Colors.sortie : Colors.silver }]}>
                    {hasOut ? fmtN(l.sortie_ambiant) : '—'}
                  </Text>
                  <Text style={[styles.tdQte, { width: 72, fontWeight: '700', color: Colors.ink }]}>
                    {fmtN(l.stock_ambiant)}
                  </Text>
                </View>
              );
            })
          )}

          {/* Ligne totaux */}
          {lignes.length > 0 && (
            <View style={styles.totalsRow}>
              <Text style={[styles.totLabel, { width: 44 + 1 + 150 }]}>TOTAUX</Text>
              <Text style={[styles.totVal, { width: 72, color: Colors.entree }]}>
                {fmtN(entrees)}
              </Text>
              <Text style={[styles.totVal, { width: 72, color: Colors.sortie }]}>
                {fmtN(sorties)}
              </Text>
              <Text style={[styles.totVal, { width: 72, color: Colors.navy }]}>
                {fmtN(stock)}
              </Text>
            </View>
          )}
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* ── Modal sélecteur produit ──────────────────────────────── */}
      <Modal
        visible={showProduitModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowProduitModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>Choisir un produit</Text>

            {/* Option "Tous" */}
            <TouchableOpacity
              style={[styles.modalOpt, !selectedProduit && styles.modalOptActive]}
              onPress={() => { setSelectedProduit(null); setShowProduitModal(false); }}
            >
              <Ionicons name="apps-outline" size={16} color={!selectedProduit ? Colors.navy : Colors.slate} />
              <Text style={[styles.modalOptText, !selectedProduit && styles.modalOptTextActive]}>
                Tous les produits
              </Text>
              {!selectedProduit && <Ionicons name="checkmark" size={18} color={Colors.navy} />}
            </TouchableOpacity>

            <FlatList
              data={produits}
              keyExtractor={(item) => String(item.id)}
              renderItem={({ item }) => {
                const active = selectedProduit?.id === item.id;
                return (
                  <TouchableOpacity
                    style={[styles.modalOpt, active && styles.modalOptActive]}
                    onPress={() => { setSelectedProduit(item); setShowProduitModal(false); }}
                  >
                    <View style={[styles.sigleDot, { backgroundColor: Colors.navy + (active ? 'ff' : '30') }]}>
                      <Text style={[styles.sigleDotText, { color: active ? Colors.white : Colors.navy }]}>
                        {item.sigle?.slice(0, 2) ?? item.nom.slice(0, 2)}
                      </Text>
                    </View>
                    <Text style={[styles.modalOptText, active && styles.modalOptTextActive]}>
                      {item.nom}
                    </Text>
                    {active && <Ionicons name="checkmark" size={18} color={Colors.navy} />}
                  </TouchableOpacity>
                );
              }}
            />

            <TouchableOpacity
              style={styles.modalClose}
              onPress={() => setShowProduitModal(false)}
            >
              <Text style={styles.modalCloseText}>Fermer</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

// ── Styles ─────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },

  // Navbar
  navbar: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.white,
    paddingHorizontal: 12, paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
    gap: 8,
  },
  backBtn: {
    width: 38, height: 38, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
  },
  navCenter: { flex: 1 },
  navTitle:  { fontSize: FontSize.md, fontWeight: '800', color: Colors.ink },
  navSub:    { fontSize: 10, color: Colors.slate },
  pdfBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: Colors.navy, borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 7,
  },
  pdfBtnDisabled: { backgroundColor: Colors.slate },
  pdfBtnText: { color: Colors.white, fontSize: 12, fontWeight: '700' },

  // Filtres
  filtersBar: {
    backgroundColor: Colors.white,
    paddingHorizontal: 14, paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
    gap: 10,
  },
  produitBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: Colors.navyTint,
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8,
  },
  produitBtnText: { flex: 1, fontSize: 13, fontWeight: '700', color: Colors.navy },

  segmented: {
    flexDirection: 'row', backgroundColor: Colors.cloud,
    borderRadius: 10, padding: 3,
  },
  segBtn: { flex: 1, paddingVertical: 6, borderRadius: 8, alignItems: 'center' },
  segBtnActive: {
    backgroundColor: Colors.white,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 1,
  },
  segText:       { fontSize: 11, fontWeight: '700', color: Colors.slate },
  segTextActive: { color: Colors.navy },

  // KPI
  kpiRow: {
    flexDirection: 'row', gap: 10,
    padding: 14,
  },
  kpi: {
    backgroundColor: Colors.white, borderRadius: 16, padding: 14,
    alignItems: 'center',
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 4, elevation: 2,
  },
  kpiMain: { flex: 1.2, backgroundColor: Colors.navy },
  kpiLabel: { fontSize: 10, color: Colors.white + 'b0', fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.3 },
  kpiValue: { fontSize: 26, fontWeight: '800', color: Colors.white, marginVertical: 2 },
  kpiUnit:  { fontSize: 10, color: Colors.white + '80' },
  kpiRight: { flex: 1, gap: 10 },
  kpiSmall: {
    flex: 1, backgroundColor: Colors.white,
    borderRadius: 14, padding: 10,
    alignItems: 'center', borderWidth: 1.5,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 2, elevation: 1,
  },
  kpiSmallVal: { fontSize: 13, fontWeight: '800', marginVertical: 2 },
  kpiSmallLbl: { fontSize: 9, color: Colors.slate, fontWeight: '600' },

  // Table
  tableWrap: {
    backgroundColor: Colors.white,
    marginHorizontal: 14, marginBottom: 14,
    borderRadius: 18, overflow: 'hidden',
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 4, elevation: 2,
  },
  tableHeader: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 14, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
    gap: 8,
  },
  tableTitle: { flex: 1, fontSize: 13, fontWeight: '800', color: Colors.ink },
  countChip: {
    backgroundColor: Colors.navy, borderRadius: 10,
    paddingHorizontal: 8, paddingVertical: 2,
  },
  countText: { color: Colors.white, fontSize: 10, fontWeight: '700' },

  colHead: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.navyTint,
    paddingHorizontal: 10, paddingVertical: 8,
  },
  th: { fontSize: 9, fontWeight: '800', color: Colors.navy, textTransform: 'uppercase', letterSpacing: 0.3 },

  row: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 10, paddingVertical: 9,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud + '80',
  },
  rowAlt: { backgroundColor: Colors.paper },
  tdDate: { fontSize: 10, color: Colors.slate },
  tdRef:  { fontSize: 11, fontWeight: '700', color: Colors.ink },
  tdType: { fontSize: 9, fontWeight: '700', textTransform: 'uppercase', marginTop: 1 },
  tdQte:  { fontSize: 11, textAlign: 'right', fontWeight: '600' },

  totalsRow: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.navy,
    paddingHorizontal: 10, paddingVertical: 9,
  },
  totLabel: { fontSize: 10, fontWeight: '800', color: Colors.white },
  totVal:   { fontSize: 11, fontWeight: '800', textAlign: 'right' },

  empty: {
    alignItems: 'center', justifyContent: 'center',
    padding: 40, gap: 10,
  },
  emptyText: { fontSize: 13, color: Colors.slate, textAlign: 'center' },

  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: '#00000060',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: Colors.white,
    borderTopLeftRadius: Radius.xl, borderTopRightRadius: Radius.xl,
    padding: 20, maxHeight: '70%',
  },
  modalHandle: {
    width: 40, height: 4, borderRadius: 2,
    backgroundColor: Colors.mist,
    alignSelf: 'center', marginBottom: 16,
  },
  modalTitle: { fontSize: 16, fontWeight: '800', color: Colors.ink, marginBottom: 12 },
  modalOpt: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  modalOptActive: { backgroundColor: Colors.navyTint, borderRadius: 10, paddingHorizontal: 8 },
  modalOptText: { flex: 1, fontSize: 14, color: Colors.ink },
  modalOptTextActive: { color: Colors.navy, fontWeight: '700' },
  sigleDot: {
    width: 32, height: 32, borderRadius: 8,
    alignItems: 'center', justifyContent: 'center',
  },
  sigleDotText: { fontSize: 10, fontWeight: '800' },
  modalClose: {
    alignItems: 'center', padding: 14, marginTop: 8,
    backgroundColor: Colors.cloud, borderRadius: 12,
  },
  modalCloseText: { fontSize: 14, fontWeight: '700', color: Colors.slate },
});
