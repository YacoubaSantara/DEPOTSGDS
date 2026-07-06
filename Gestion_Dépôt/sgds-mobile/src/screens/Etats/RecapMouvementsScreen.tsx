import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, RefreshControl, Modal, FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import dayjs from 'dayjs';

import { etatsApi, RecapResponse, RecapFilters, Periode } from '../../api/etats';
import { Colors, FontSize, Radius } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';
import { buildRecapHtml } from '../../utils/pdfTemplate';

// ── Constantes ────────────────────────────────────────────────────

const PERIODS = [
  { label: '7j',   days: 7 },
  { label: '30j',  days: 30 },
  { label: '3m',   days: 90 },
  { label: '12m',  days: 365 },
  { label: 'Tout', days: null },
];

function fmtN(n: any): string {
  const v = Number(n);
  if (isNaN(v)) return '0';
  return v.toLocaleString('fr-FR', { maximumFractionDigits: 0 });
}

function fmtVol(n: number): string {
  if (isNaN(n)) return '0';
  return Math.round(n).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
}

// ── Composant ─────────────────────────────────────────────────────

export function RecapMouvementsScreen() {
  const navigation = useNavigation();

  const [period, setPeriod]             = useState('30j');
  const [periodes, setPeriodes]         = useState<Periode[]>([]);
  const [selectedPeriode, setSelectedPeriode] = useState<Periode | null>(null);
  const [showPeriodeModal, setShowPeriodeModal] = useState(false);
  const [data, setData]                 = useState<RecapResponse | null>(null);
  const [loading, setLoading]           = useState(true);
  const [refreshing, setRefreshing]     = useState(false);
  const [error, setError]               = useState<string | null>(null);
  const [generatingPdf, setGeneratingPdf] = useState(false);

  useEffect(() => {
    etatsApi.periodes().then(r => setPeriodes(r.data)).catch(() => {});
  }, []);

  const buildFilters = useCallback((): RecapFilters => {
    if (selectedPeriode) {
      // La période comptable prime sur la plage rapide : elle ajoute aussi
      // le stock d'ouverture (report) comme point de départ du stock final.
      return { periode_id: selectedPeriode.id };
    }
    const p = PERIODS.find(x => x.label === period);
    if (!p?.days) return {};
    return {
      date_debut: dayjs().subtract(p.days, 'day').format('YYYY-MM-DD'),
      date_fin:   dayjs().format('YYYY-MM-DD'),
    };
  }, [period, selectedPeriode]);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError(null);
    try {
      const res = await etatsApi.recap(buildFilters());
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
      let periodeLabel: string;
      if (selectedPeriode) {
        periodeLabel = selectedPeriode.nom;
      } else {
        const p = PERIODS.find(x => x.label === period);
        periodeLabel = p?.days
          ? `Derniers ${period} — du ${dayjs().subtract(p.days, 'day').format('DD/MM/YYYY')} au ${dayjs().format('DD/MM/YYYY')}`
          : 'Tous les mouvements';
      }

      const html = buildRecapHtml({
        marketeurNom: data.marketeur_nom,
        periodeLabel,
        par_produit:  data.par_produit,
        totaux:       data.totaux,
        generatedAt:  dayjs().format('DD/MM/YYYY HH:mm'),
      });

      const { uri } = await Print.printToFileAsync({ html, base64: false });
      const canShare = await Sharing.isAvailableAsync();

      if (canShare) {
        await Sharing.shareAsync(uri, {
          mimeType: 'application/pdf',
          dialogTitle: 'Récapitulatif — SGDS',
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

  if (loading) return <LoadingSpinner fullScreen message="Chargement du récapitulatif..." />;
  if (error)   return <ErrorMessage message={error} onRetry={() => fetchData()} />;

  const t = data?.totaux;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* ── Navbar ──────────────────────────────────────────────── */}
      <View style={styles.navbar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color={Colors.ink} />
        </TouchableOpacity>
        <View style={styles.navCenter}>
          <Text style={styles.navTitle}>Récapitulatif</Text>
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
        {/* ── Filtre période ──────────────────────────────────── */}
        <View style={styles.filterBar}>
          <TouchableOpacity
            style={[styles.periodeBtn, selectedPeriode && styles.periodeBtnActive]}
            onPress={() => setShowPeriodeModal(true)}
          >
            <Ionicons name="calendar-outline" size={14} color={selectedPeriode ? Colors.white : Colors.navy} />
            <Text style={[styles.periodeBtnText, selectedPeriode && styles.periodeBtnTextActive]} numberOfLines={1}>
              {selectedPeriode?.nom ?? 'Période comptable'}
            </Text>
            {selectedPeriode ? (
              <TouchableOpacity onPress={() => setSelectedPeriode(null)} hitSlop={8}>
                <Ionicons name="close-circle" size={14} color={Colors.white} />
              </TouchableOpacity>
            ) : (
              <Ionicons name="chevron-down" size={12} color={Colors.slate} />
            )}
          </TouchableOpacity>

          <View style={[styles.segmented, selectedPeriode && styles.segmentedDisabled]}>
            {PERIODS.map(p => (
              <TouchableOpacity
                key={p.label}
                onPress={() => { setSelectedPeriode(null); setPeriod(p.label); }}
                style={[styles.segBtn, !selectedPeriode && period === p.label && styles.segBtnActive]}
                activeOpacity={0.8}
              >
                <Text style={[styles.segText, !selectedPeriode && period === p.label && styles.segTextActive]}>
                  {p.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* ── Stock d'ouverture (report) ──────────────────────── */}
        {selectedPeriode && (
          <View style={styles.reportBanner}>
            <Ionicons name="arrow-redo-outline" size={16} color={Colors.navy} />
            <Text style={styles.reportText}>
              Stock d'ouverture (report) : <Text style={styles.reportValue}>{fmtVol(Number(t?.stock_ouverture_ambiant ?? 0))} L</Text>
            </Text>
          </View>
        )}

        {/* ── KPI globaux ──────────────────────────────────────── */}
        <View style={styles.kpiSection}>
          <View style={[styles.kpiBig, { backgroundColor: Colors.navy }]}>
            <Text style={styles.kpiBigLabel}>Total mouvements</Text>
            <Text style={styles.kpiBigVal}>{t?.nb_mouvements ?? 0}</Text>
            <Text style={styles.kpiBigSub}>
              Stock final : {fmtVol(Number(t?.stock_final_ambiant ?? 0))} L
            </Text>
          </View>
          <View style={styles.kpiSmallRow}>
            <KpiSmall
              label="Entrées"
              nb={t?.nb_entrees ?? 0}
              vol={Number(t?.volume_entree_ambiant ?? 0)}
              color={Colors.entree}
              icon="arrow-down-circle"
            />
            <KpiSmall
              label="Sorties"
              nb={t?.nb_sorties ?? 0}
              vol={Number(t?.volume_sortie_ambiant ?? 0)}
              color={Colors.sortie}
              icon="arrow-up-circle"
            />
          </View>
          {(t?.nb_cessions ?? 0) > 0 && (
            <View style={styles.kpiSmallRow}>
              <KpiSmall
                label="Cessions"
                nb={t?.nb_cessions ?? 0}
                vol={Number(t?.volume_cession_ambiant ?? 0)}
                color={Colors.cession}
                icon="swap-horizontal"
              />
              {(t?.nb_acquittements ?? 0) > 0 && (
                <KpiSmall
                  label="Acquittements"
                  nb={t?.nb_acquittements ?? 0}
                  vol={Number(t?.volume_acquit_ambiant ?? 0)}
                  color={Colors.acquittement}
                  icon="checkmark-circle"
                />
              )}
            </View>
          )}
        </View>

        {/* ── Par produit ─────────────────────────────────────── */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Détail par produit</Text>
          <View style={styles.countChip}>
            <Text style={styles.countText}>{data?.par_produit.length ?? 0}</Text>
          </View>
        </View>

        {data?.par_produit.length === 0 ? (
          <View style={styles.empty}>
            <Ionicons name="document-outline" size={36} color={Colors.silver} />
            <Text style={styles.emptyText}>Aucun mouvement sur cette période</Text>
          </View>
        ) : (
          data?.par_produit.map((pr, i) => (
            <View key={pr.produit_id} style={styles.prodCard}>
              {/* En-tête produit */}
              <View style={styles.prodHeader}>
                <View style={styles.prodBadge}>
                  <Text style={styles.prodBadgeText}>{pr.produit_sigle}</Text>
                </View>
                <Text style={styles.prodNom}>{pr.produit_nom}</Text>
                <View style={[styles.stockFinal, Number(pr.stock_final_ambiant) >= 0 ? styles.stockPos : styles.stockNeg]}>
                  <Text style={styles.stockFinalVal}>
                    {fmtVol(Number(pr.stock_final_ambiant))} L
                  </Text>
                </View>
              </View>

              {/* Lignes stats */}
              <View style={styles.prodStats}>
                {pr.nb_entrees > 0 && (
                  <StatRow
                    icon="arrow-down"
                    label="Entrées"
                    nb={pr.nb_entrees}
                    vol={Number(pr.volume_entree_ambiant)}
                    color={Colors.entree}
                  />
                )}
                {pr.nb_sorties > 0 && (
                  <StatRow
                    icon="arrow-up"
                    label="Sorties"
                    nb={pr.nb_sorties}
                    vol={Number(pr.volume_sortie_ambiant)}
                    color={Colors.sortie}
                  />
                )}
                {pr.nb_cessions > 0 && (
                  <StatRow
                    icon="swap-horizontal"
                    label="Cessions"
                    nb={pr.nb_cessions}
                    vol={Number(pr.volume_cession_ambiant)}
                    color={Colors.cession}
                  />
                )}
                {pr.nb_acquittements > 0 && (
                  <StatRow
                    icon="checkmark-circle-outline"
                    label="Acquittements"
                    nb={pr.nb_acquittements}
                    vol={Number(pr.volume_acquit_ambiant)}
                    color={Colors.acquittement}
                  />
                )}
              </View>
            </View>
          ))
        )}

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* ── Modal sélecteur période comptable ─────────────────────── */}
      <Modal visible={showPeriodeModal} transparent animationType="slide" onRequestClose={() => setShowPeriodeModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>Choisir une période comptable</Text>
            <Text style={styles.modalHint}>
              Affiche le stock d'ouverture (report) et les mouvements de la période sélectionnée.
            </Text>
            <FlatList
              data={periodes}
              keyExtractor={(item) => String(item.id)}
              renderItem={({ item }) => {
                const active = selectedPeriode?.id === item.id;
                return (
                  <TouchableOpacity
                    style={[styles.modalOpt, active && styles.modalOptActive]}
                    onPress={() => { setSelectedPeriode(item); setShowPeriodeModal(false); }}
                  >
                    <Ionicons name="calendar" size={16} color={active ? Colors.navy : Colors.slate} />
                    <Text style={[styles.modalOptText, active && styles.modalOptTextActive]}>{item.nom}</Text>
                    {item.statut === 'CLOTUREE' && (
                      <View style={styles.clotureBadge}>
                        <Text style={styles.clotureBadgeText}>CLÔTURÉE</Text>
                      </View>
                    )}
                    {active && <Ionicons name="checkmark" size={18} color={Colors.navy} />}
                  </TouchableOpacity>
                );
              }}
            />
            <TouchableOpacity style={styles.modalClose} onPress={() => setShowPeriodeModal(false)}>
              <Text style={styles.modalCloseText}>Fermer</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

// ── Sous-composants ───────────────────────────────────────────────

function KpiSmall({
  label, nb, vol, color, icon,
}: { label: string; nb: number; vol: number; color: string; icon: any }) {
  return (
    <View style={[kpiSmallStyles.card, { borderColor: color + '30' }]}>
      <View style={[kpiSmallStyles.iconWrap, { backgroundColor: color + '18' }]}>
        <Ionicons name={icon} size={14} color={color} />
      </View>
      <Text style={kpiSmallStyles.label}>{label}</Text>
      <Text style={[kpiSmallStyles.val, { color }]}>{fmtVol(vol)} L</Text>
      <Text style={kpiSmallStyles.nb}>{nb} mvt</Text>
    </View>
  );
}

const kpiSmallStyles = StyleSheet.create({
  card: {
    flex: 1, backgroundColor: Colors.white,
    borderRadius: 14, padding: 12,
    alignItems: 'center', borderWidth: 1.5,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 2, elevation: 1,
  },
  iconWrap: { width: 30, height: 30, borderRadius: 8, alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
  label: { fontSize: 9, color: Colors.slate, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.3 },
  val:   { fontSize: 14, fontWeight: '800', marginVertical: 1 },
  nb:    { fontSize: 9, color: Colors.slate },
});

function StatRow({
  icon, label, nb, vol, color,
}: { icon: any; label: string; nb: number; vol: number; color: string }) {
  return (
    <View style={statRowStyles.row}>
      <View style={[statRowStyles.dot, { backgroundColor: color + '20' }]}>
        <Ionicons name={icon} size={12} color={color} />
      </View>
      <Text style={statRowStyles.label}>{label}</Text>
      <Text style={statRowStyles.nb}>{nb} mvt</Text>
      <Text style={[statRowStyles.vol, { color }]}>{fmtN(vol)} L</Text>
    </View>
  );
}

const statRowStyles = StyleSheet.create({
  row: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 8, gap: 8,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  dot: { width: 24, height: 24, borderRadius: 7, alignItems: 'center', justifyContent: 'center' },
  label: { flex: 1, fontSize: 12, color: Colors.ink, fontWeight: '600' },
  nb:    { fontSize: 10, color: Colors.slate },
  vol:   { fontSize: 13, fontWeight: '800', minWidth: 80, textAlign: 'right' },
});

// ── Styles ────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },

  navbar: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.white,
    paddingHorizontal: 12, paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
    gap: 8,
  },
  backBtn: { width: 38, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
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

  filterBar: {
    backgroundColor: Colors.white,
    paddingHorizontal: 14, paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
    gap: 10,
  },
  periodeBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: Colors.navyTint,
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8,
  },
  periodeBtnActive:     { backgroundColor: Colors.navy },
  periodeBtnText:       { flex: 1, fontSize: 13, fontWeight: '700', color: Colors.navy },
  periodeBtnTextActive: { color: Colors.white },
  segmented: {
    flexDirection: 'row', backgroundColor: Colors.cloud,
    borderRadius: 10, padding: 3,
  },
  segmentedDisabled: { opacity: 0.5 },
  segBtn: { flex: 1, paddingVertical: 6, borderRadius: 8, alignItems: 'center' },
  segBtnActive: {
    backgroundColor: Colors.white,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 1,
  },
  segText:       { fontSize: 11, fontWeight: '700', color: Colors.slate },
  segTextActive: { color: Colors.navy },

  reportBanner: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: Colors.navyTint,
    marginHorizontal: 14, marginTop: 12,
    borderRadius: 12, paddingHorizontal: 12, paddingVertical: 10,
  },
  reportText:  { flex: 1, fontSize: 12, color: Colors.navy, fontWeight: '600' },
  reportValue: { fontWeight: '800' },

  // Modal sélecteur période
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
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
  modalTitle: { fontSize: 16, fontWeight: '800', color: Colors.ink, marginBottom: 4 },
  modalHint:  { fontSize: 11, color: Colors.slate, marginBottom: 12, lineHeight: 16 },
  modalOpt: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  modalOptActive: { backgroundColor: Colors.navyTint, borderRadius: 10, paddingHorizontal: 8 },
  modalOptText: { flex: 1, fontSize: 14, color: Colors.ink },
  modalOptTextActive: { color: Colors.navy, fontWeight: '700' },
  clotureBadge: { backgroundColor: Colors.cloud, borderRadius: 5, paddingHorizontal: 6, paddingVertical: 2 },
  clotureBadgeText: { fontSize: 9, fontWeight: '700', color: Colors.slate },
  modalClose: {
    alignItems: 'center', padding: 14, marginTop: 8,
    backgroundColor: Colors.cloud, borderRadius: 12,
  },
  modalCloseText: { fontSize: 14, fontWeight: '700', color: Colors.slate },

  kpiSection: { padding: 14, gap: 10 },
  kpiBig: {
    borderRadius: 18, padding: 16,
    shadowColor: Colors.navy,
    shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.15, shadowRadius: 12, elevation: 4,
  },
  kpiBigLabel: { color: Colors.white + 'b0', fontSize: 10, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.4 },
  kpiBigVal:   { color: Colors.white, fontSize: 32, fontWeight: '800', marginVertical: 2 },
  kpiBigSub:   { color: Colors.white + '80', fontSize: 11 },
  kpiSmallRow: { flexDirection: 'row', gap: 10 },

  sectionHeader: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingHorizontal: 16, paddingTop: 4, paddingBottom: 10,
  },
  sectionTitle: { flex: 1, fontSize: 14, fontWeight: '800', color: Colors.ink },
  countChip: {
    backgroundColor: Colors.navy, borderRadius: 10,
    paddingHorizontal: 8, paddingVertical: 2,
  },
  countText: { color: Colors.white, fontSize: 10, fontWeight: '700' },

  prodCard: {
    backgroundColor: Colors.white,
    marginHorizontal: 14, marginBottom: 12,
    borderRadius: 18,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 4, elevation: 2,
    overflow: 'hidden',
  },
  prodHeader: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 14, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
    gap: 8,
  },
  prodBadge: {
    backgroundColor: Colors.navy, borderRadius: 6,
    paddingHorizontal: 8, paddingVertical: 3,
  },
  prodBadgeText: { color: Colors.white, fontWeight: '800', fontSize: 11 },
  prodNom: { flex: 1, fontSize: 14, fontWeight: '700', color: Colors.ink },
  stockFinal: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  stockPos: { backgroundColor: Colors.greenSoft },
  stockNeg: { backgroundColor: Colors.redSoft },
  stockFinalVal: { fontSize: 12, fontWeight: '800', color: Colors.ink },

  prodStats: { paddingHorizontal: 14, paddingBottom: 4 },

  empty: {
    alignItems: 'center', justifyContent: 'center',
    padding: 40, gap: 10,
  },
  emptyText: { fontSize: 13, color: Colors.slate, textAlign: 'center' },
});
