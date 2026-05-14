import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';

import { etatsApi, StockGlobalResponse } from '../../api/etats';
import { Colors, Radius, FontSize } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';

const PERIODS = ['7j', '30j', '3m', '12m'] as const;
type Period = typeof PERIODS[number];

function fmtN(n: any, dec = 0): string {
  const v = Number(n);
  if (isNaN(v)) return '0';
  return v.toLocaleString('fr-FR', { maximumFractionDigits: dec });
}
function fmtCompact(n: number): string {
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1).replace('.0', '') + 'M';
  if (Math.abs(n) >= 1_000)     return (n / 1_000).toFixed(1).replace('.0', '') + 'k';
  return String(n);
}

export function EtatsScreen() {
  const [data, setData]           = useState<StockGlobalResponse | null>(null);
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [period, setPeriod]       = useState<Period>('30j');

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError(null);
    try {
      const res = await etatsApi.stockGlobal({});
      setData(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { fetchData(); }, [fetchData]));

  if (loading) return <LoadingSpinner fullScreen message="Chargement des états..." />;
  if (error)   return <ErrorMessage message={error} onRetry={() => fetchData()} />;

  const lignes   = data?.lignes ?? [];
  const totalAmb = data?.stock_final_ambiant ?? 0;
  const total15  = data?.stock_final_15 ?? 0;
  const entrees  = data?.cumul_entrees_ambiant ?? 0;
  const sorties  = data?.cumul_sorties_ambiant ?? 0;

  // Construire les données pour le graphique barres à partir des stocks dans lignes
  const stockHistory = lignes.map(l => l.stock_ambiant).filter(v => v > 0);
  const maxStockHistory = Math.max(...stockHistory, 1);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
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
        {/* ── EN-TÊTE ───────────────────────────────────────── */}
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <View>
              <Text style={styles.headerSub}>Rapport</Text>
              <Text style={styles.headerTitle}>État du stock</Text>
            </View>
            <View style={styles.headerActions}>
              <TouchableOpacity style={styles.iconBtn}>
                <Ionicons name="calendar-outline" size={16} color={Colors.ink} />
              </TouchableOpacity>
              <TouchableOpacity style={styles.iconBtn}>
                <Ionicons name="download-outline" size={16} color={Colors.ink} />
              </TouchableOpacity>
            </View>
          </View>

          {/* Segmented period */}
          <View style={styles.segmented}>
            {PERIODS.map(p => (
              <TouchableOpacity
                key={p}
                onPress={() => setPeriod(p)}
                style={[styles.segBtn, period === p && styles.segBtnActive]}
                activeOpacity={0.8}
              >
                <Text style={[styles.segText, period === p && styles.segTextActive]}>{p}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.content}>
          {/* ── RÉCAP STOCK FINAL ─────────────────────────── */}
          <LinearGradient
            colors={[Colors.navy, Colors.navyDeep]}
            style={styles.recapCard}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <View style={styles.recapGlow} />
            <Text style={styles.recapLabel}>Stock final · ambiant</Text>
            <Text style={styles.recapValue}>
              {fmtN(totalAmb)}
              <Text style={styles.recapUnit}> L</Text>
            </Text>
            <Text style={styles.recapSub}>≈ {fmtN(total15)} L à 15°C</Text>
          </LinearGradient>

          {/* ── FLUX ENTRÉES / SORTIES ─────────────────────── */}
          <View style={styles.flowGrid}>
            <FlowCard label="Entrées" value={entrees} color={Colors.entree} iconName="arrow-down" />
            <FlowCard label="Sorties" value={sorties} color={Colors.sortie} iconName="arrow-up" />
          </View>

          {/* ── ÉVOLUTION DU STOCK ────────────────────────── */}
          {stockHistory.length > 1 && (
            <>
              <SectionHeader title="Évolution du stock" subtitle={`${stockHistory.length} points`} />
              <View style={styles.chartCard}>
                <View style={styles.barChart}>
                  {stockHistory.slice(-8).map((v, i) => {
                    const pct   = (v / maxStockHistory) * 100;
                    const color = Colors.navy;
                    return (
                      <View key={i} style={styles.barCol}>
                        <Text style={styles.barValue}>{fmtCompact(v)}</Text>
                        <View style={styles.barTrack}>
                          <View style={[
                            styles.barFill,
                            { height: `${Math.max(pct, 5)}%` as any, backgroundColor: color },
                          ]} />
                        </View>
                        <Text style={styles.barLabel}>{i + 1}</Text>
                      </View>
                    );
                  })}
                </View>
              </View>
            </>
          )}

          {/* ── TABLEAU MOUVEMENTS ────────────────────────── */}
          <SectionHeader title="Mouvements détaillés" action="Exporter" />
          <View style={styles.tableCard}>
            {/* Entête */}
            <View style={styles.tableHead}>
              <Text style={[styles.thText, { width: 62 }]}>Date</Text>
              <Text style={[styles.thText, { flex: 1 }]}>Réf.</Text>
              <Text style={[styles.thText, { width: 70, textAlign: 'right' }]}>Entrée</Text>
              <Text style={[styles.thText, { width: 70, textAlign: 'right' }]}>Sortie</Text>
            </View>
            {lignes.slice(0, 12).map((l, i) => {
              const dt  = l.date ? l.date.slice(8, 10) + '/' + l.date.slice(5, 7) : '—';
              const hasIn  = l.entree_ambiant > 0;
              const hasOut = l.sortie_ambiant > 0;
              return (
                <View key={i} style={[styles.tableRow, i % 2 === 1 && styles.tableRowAlt]}>
                  <Text style={[styles.tdDate, { width: 62 }]}>{dt}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.tdSigle} numberOfLines={1}>{l.reference || l.type}</Text>
                    <Text style={[styles.tdType, { color: Colors.slate }]}>{fmtN(l.stock_ambiant)} L</Text>
                  </View>
                  <Text style={[
                    styles.tdQte, { width: 70, color: hasIn ? Colors.entree : Colors.silver },
                  ]}>{hasIn ? fmtN(l.entree_ambiant) : '—'}</Text>
                  <Text style={[
                    styles.tdQte, { width: 70, color: hasOut ? Colors.sortie : Colors.silver },
                  ]}>{hasOut ? fmtN(l.sortie_ambiant) : '—'}</Text>
                </View>
              );
            })}
            {lignes.length === 0 && (
              <Text style={[styles.emptyText, { padding: 16 }]}>Aucun mouvement</Text>
            )}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Sous-composants ────────────────────────────────────────────

function SectionHeader({
  title, subtitle, action,
}: { title: string; subtitle?: string; action?: string; }) {
  return (
    <View style={styles.sectionHeader}>
      <View>
        <Text style={styles.sectionTitle}>{title}</Text>
        {subtitle && <Text style={styles.sectionSub}>{subtitle}</Text>}
      </View>
      {action && <Text style={styles.sectionAction}>{action}</Text>}
    </View>
  );
}

function FlowCard({
  label, value, color, iconName,
}: { label: string; value: number; color: string; iconName: any; }) {
  return (
    <View style={styles.flowCard}>
      <View style={styles.flowTop}>
        <View style={[styles.flowIcon, { backgroundColor: color + '1a' }]}>
          <Ionicons name={iconName} size={13} color={color} />
        </View>
        <Text style={styles.flowLabel}>{label}</Text>
      </View>
      <Text style={styles.flowValue}>{fmtN(value)}</Text>
      <Text style={styles.flowUnit}>litres ambiant</Text>
    </View>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: Colors.paper },
  content: { padding: 16, gap: 0 },

  // Header
  header: {
    backgroundColor: Colors.white,
    paddingHorizontal: 20, paddingTop: 14, paddingBottom: 14,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  headerTop: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 14,
  },
  headerSub:     { fontSize: 11, color: Colors.slate, fontWeight: '600' },
  headerTitle:   { fontSize: 22, fontWeight: '800', color: Colors.ink, letterSpacing: -0.4, marginTop: 1 },
  headerActions: { flexDirection: 'row', gap: 8 },
  iconBtn: {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: Colors.cloud,
    alignItems: 'center', justifyContent: 'center',
  },

  // Segmented
  segmented: {
    flexDirection: 'row', backgroundColor: Colors.cloud,
    borderRadius: 10, padding: 3,
  },
  segBtn: {
    flex: 1, paddingVertical: 7, borderRadius: 8,
    alignItems: 'center',
  },
  segBtnActive: {
    backgroundColor: Colors.white,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 1,
  },
  segText:       { fontSize: 12, fontWeight: '700', color: Colors.slate },
  segTextActive: { color: Colors.navy },

  // Récap card
  recapCard: {
    borderRadius: 20, padding: 18, marginTop: 16,
    shadowColor: Colors.navy,
    shadowOffset: { width: 0, height: 16 }, shadowOpacity: 0.20, shadowRadius: 28, elevation: 8,
    overflow: 'hidden',
  },
  recapGlow: {
    position: 'absolute', right: -30, top: -30,
    width: 140, height: 140, borderRadius: 70,
    backgroundColor: Colors.orange + '22',
  },
  recapLabel: { color: Colors.white + 'b3', fontSize: 11, fontWeight: '600', letterSpacing: 0.4, textTransform: 'uppercase' },
  recapValue: { color: Colors.white, fontSize: 30, fontWeight: '800', letterSpacing: -1, marginTop: 4 },
  recapUnit:  { fontSize: 14, fontWeight: '600', opacity: 0.8 },
  recapSub:   { color: Colors.white + 'b3', fontSize: 11, marginTop: 3 },

  // Flow cards
  flowGrid: { flexDirection: 'row', gap: 10, marginTop: 12 },
  flowCard: {
    flex: 1, backgroundColor: Colors.white,
    borderRadius: 20, padding: 14,
    borderWidth: 1, borderColor: Colors.cloud,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  flowTop:   { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  flowIcon:  { width: 26, height: 26, borderRadius: 7, alignItems: 'center', justifyContent: 'center' },
  flowLabel: { fontSize: 11, color: Colors.slate, fontWeight: '600' },
  flowValue: { fontSize: 18, fontWeight: '800', color: Colors.ink },
  flowUnit:  { fontSize: 10, color: Colors.slate },

  // Section header
  sectionHeader: {
    flexDirection: 'row', alignItems: 'flex-end',
    justifyContent: 'space-between',
    paddingTop: 22, paddingBottom: 10,
  },
  sectionTitle:  { fontSize: 14, fontWeight: '800', color: Colors.ink, letterSpacing: -0.2 },
  sectionSub:    { fontSize: 11, color: Colors.slate, marginTop: 1 },
  sectionAction: { fontSize: 12, fontWeight: '700', color: Colors.navy },

  // Bar chart
  chartCard: {
    backgroundColor: Colors.white, borderRadius: 20, padding: 16,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  barChart: { flexDirection: 'row', alignItems: 'flex-end', height: 160, gap: 14 },
  barCol:   { flex: 1, alignItems: 'center', gap: 6, height: '100%', justifyContent: 'flex-end' },
  barValue: { fontSize: 9, fontWeight: '700', color: Colors.ink },
  barTrack: { width: '100%', flex: 1, justifyContent: 'flex-end' },
  barFill:  { width: '100%', borderRadius: 8, minHeight: 8 },
  barLabel: { fontSize: 9, color: Colors.slate, fontWeight: '700' },

  // Table
  tableCard: {
    backgroundColor: Colors.white, borderRadius: 20,
    overflow: 'hidden',
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
    marginBottom: 16,
  },
  tableHead: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.navy,
    paddingHorizontal: 12, paddingVertical: 10,
  },
  thText: {
    color: Colors.white, fontSize: 10, fontWeight: '800',
    letterSpacing: 0.6, textTransform: 'uppercase',
  },
  tableRow: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 12, paddingVertical: 10,
    backgroundColor: Colors.white,
    borderTopWidth: 1, borderTopColor: Colors.cloud,
  },
  tableRowAlt: { backgroundColor: Colors.paper },
  tdDate:  { color: Colors.slate, fontSize: 11 },
  tdSigle: { fontSize: 11, fontWeight: '700', color: Colors.ink },
  tdType:  { fontSize: 9, fontWeight: '700' },
  tdQte:   { fontSize: 11, fontWeight: '700', textAlign: 'right' },
  emptyText: { color: Colors.slate, fontSize: FontSize.sm, textAlign: 'center' },
});
