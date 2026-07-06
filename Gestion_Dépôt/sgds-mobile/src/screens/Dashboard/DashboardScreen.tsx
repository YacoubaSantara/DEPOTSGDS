import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';

import { dashboardApi, DashboardData, DernierMouvement } from '../../api/dashboard';
import { notificationsApi } from '../../api/notifications';
import type { TabParams } from '../../navigation/AppNavigator';
import { useAuth } from '../../context/AuthContext';
import { Colors, FontSize, Spacing, Radius, TypeMeta } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';

function fmtN(n: number | null | undefined, dec = 0): string {
  const v = Number(n);
  if (isNaN(v)) return '0';
  return v.toLocaleString('fr-FR', { maximumFractionDigits: dec, minimumFractionDigits: dec });
}

export function DashboardScreen() {
  const { user } = useAuth();
  const navigation = useNavigation<BottomTabNavigationProp<TabParams, 'Dashboard'>>();

  const [data, setData]             = useState<DashboardData | null>(null);
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const [notifCount, setNotifCount] = useState(0);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError(null);
    try {
      const res = await dashboardApi.get();
      setData(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const fetchNotifCount = useCallback(async () => {
    try {
      const res = await notificationsApi.getAll();
      setNotifCount(res.data.count_non_lues);
    } catch {
      // silencieux
    }
  }, []);

  useFocusEffect(useCallback(() => {
    fetchData();
    fetchNotifCount();
  }, [fetchData, fetchNotifCount]));

  if (loading) return <LoadingSpinner fullScreen message="Chargement..." />;
  if (error)   return <ErrorMessage message={error} onRetry={() => fetchData()} />;

  const stocks    = data?.stocks ?? [];
  const derniers  = data?.derniers_mouvements ?? [];
  const totalAmb  = stocks.reduce((s, x) => s + Number(x.stock_ambiant ?? 0), 0);
  const initials  = user?.full_name
    ? user.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : (user?.username ?? '??').slice(0, 2).toUpperCase();

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchData(true)}
            tintColor={Colors.white}
            colors={[Colors.orange]}
          />
        }
      >
        {/* ── HERO ─────────────────────────────────────────── */}
        <LinearGradient
          colors={[Colors.navySoft, Colors.navy, Colors.navyDeep]}
          style={styles.hero}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          {/* Glow blobs */}
          <View style={styles.glow1} />
          <View style={styles.glow2} />

          {/* Top row: avatar + actions */}
          <View style={styles.heroTop}>
            <View style={styles.heroLeft}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{initials}</Text>
              </View>
              <View>
                <Text style={styles.heroGreet}>Bonjour</Text>
                <Text style={styles.heroName} numberOfLines={1}>
                  {user?.full_name || user?.username}
                </Text>
              </View>
            </View>
            <View style={styles.heroActions}>
              <TouchableOpacity
                style={styles.iconBtn}
                onPress={() => navigation.navigate('Notifications')}
              >
                <Ionicons name="notifications-outline" size={18} color={Colors.white} />
                {notifCount > 0 && (
                  <View style={styles.notifBadge}>
                    <Text style={styles.notifBadgeText}>
                      {notifCount > 9 ? '9+' : notifCount}
                    </Text>
                  </View>
                )}
              </TouchableOpacity>
            </View>
          </View>

          {/* Dépôt pill */}
          {data?.marketeur_nom && (
            <View style={styles.depotPill}>
              <View style={styles.depotDot}>
                <Text style={styles.depotDotText}>P</Text>
              </View>
              <Text style={styles.depotText} numberOfLines={1}>{data.marketeur_nom}</Text>
              <Ionicons name="chevron-down" size={14} color={Colors.white + '99'} />
            </View>
          )}

          {/* Big total */}
          <View style={styles.totalBlock}>
            <Text style={styles.totalLabel}>Stock total · ambiant</Text>
            <View style={styles.totalRow}>
              <Text style={styles.totalValue}>{fmtN(totalAmb)}</Text>
              <Text style={styles.totalUnit}> L</Text>
            </View>
            <View style={styles.totalDelta}>
              <View style={styles.deltaChip}>
                <Ionicons
                  name={(data?.delta_hier ?? 0) >= 0 ? 'arrow-up' : 'arrow-down'}
                  size={11}
                  color="#7BE2A6"
                />
                <Text style={styles.deltaText}>
                  {(data?.delta_hier ?? 0) >= 0 ? '+' : ''}{data?.delta_hier ?? 0}%
                </Text>
              </View>
              <Text style={styles.deltaDate}>vs hier</Text>
            </View>
          </View>
        </LinearGradient>

        {/* ── KPI CARDS (floating) ─────────────────────────── */}
        <View style={styles.kpiWrap}>
          <View style={styles.kpiGrid}>
            <KpiCard
              label="Entrées"
              value={fmtN(data?.total_entrees ?? 0)}
              unit="L"
              delta={`${(data?.total_mouvements ?? 0) > 0 ? Math.round((data?.nb_entrees ?? 0) / (data?.total_mouvements ?? 1) * 100) : 0}%`}
              up
              color={Colors.entree}
              iconName="arrow-down"
            />
            <KpiCard
              label="Sorties"
              value={fmtN(data?.total_sorties ?? 0)}
              unit="L"
              delta={`${(data?.total_mouvements ?? 0) > 0 ? Math.round((data?.nb_sorties ?? 0) / (data?.total_mouvements ?? 1) * 100) : 0}%`}
              up={false}
              color={Colors.sortie}
              iconName="arrow-up"
            />
            <KpiCard
              label="Mouvements"
              value={String(data?.total_mouvements ?? 0)}
              unit=""
              delta={`${(data?.total_mouvements ?? 0) > 0 ? Math.round(((data?.nb_entrees ?? 0) + (data?.nb_sorties ?? 0)) / (data?.total_mouvements ?? 1) * 100) : 0}%`}
              up
              color={Colors.navy}
              iconName="swap-horizontal"
            />
            <KpiCard
              label="Taux remplissage"
              value={String(Math.round(data?.taux_remplissage ?? 0))}
              unit="%"
              delta={`${Math.round(100 - (data?.taux_remplissage ?? 0))}% libre`}
              up={(data?.taux_remplissage ?? 0) >= 35}
              color={Colors.orange}
              iconName="water"
            />
          </View>
        </View>

        {/* ── STOCKS PAR PRODUIT ───────────────────────────── */}
        <SectionHeader
          title="Stocks par produit"
          action="Voir États"
        />
        <View style={styles.pad}>
          {stocks.length > 0 ? stocks.map((s, i) => (
            <StockRow key={s.produit_id ?? i} stock={s} />
          )) : (
            <EmptyCard text="Aucun stock enregistré" />
          )}
        </View>

        {/* ── NIVEAUX DES CUVES ────────────────────────────── */}
        <SectionHeader title="Niveaux des cuves" subtitle="Capacité utilisée" />
        <View style={styles.pad}>
          <View style={styles.gaugesCard}>
            {stocks.map((s, i) => {
              const cap   = Number(s.capacite ?? 0) || 1;
              const amb   = Number(s.stock_ambiant ?? 0);
              const pct   = Math.min(Math.round((amb / cap) * 100), 100);
              const warn  = pct < 35;
              const color = STOCK_COLORS[s.produit_sigle ?? ''] ?? Colors.navy;
              return (
                <View key={s.produit_id ?? i} style={[styles.gaugeRow, i > 0 && { marginTop: 14 }]}>
                  <View style={styles.gaugeHeader}>
                    <View style={styles.gaugeTitleRow}>
                      <View style={[styles.gaugeDot, { backgroundColor: color }]} />
                      <Text style={styles.gaugeName}>{s.produit_nom}</Text>
                      <Text style={styles.gaugeSigle}>{s.produit_sigle}</Text>
                    </View>
                    <Text style={[styles.gaugePct, warn && { color: Colors.red }]}>{pct}%</Text>
                  </View>
                  <View style={styles.gaugeTrack}>
                    <View style={[styles.gaugeFill, { width: pct + '%' as any, backgroundColor: color }]} />
                  </View>
                  <View style={styles.gaugeMeta}>
                    <Text style={styles.gaugeMetaText}>{fmtN(amb)} L</Text>
                    <Text style={styles.gaugeMetaText}>/ {fmtN(cap)} L</Text>
                  </View>
                </View>
              );
            })}
          </View>
        </View>

        {/* ── ACTIVITÉ RÉCENTE ─────────────────────────────── */}
        <SectionHeader
          title="Activité récente"
          badge={data?.total_mouvements}
          action="Tout voir"
        />
        <View style={[styles.pad, { paddingBottom: 100 }]}>
          {derniers.slice(0, 5).map(m => (
            <ActivityRow key={m.id} mvt={m} />
          ))}
          {derniers.length === 0 && <EmptyCard text="Aucun mouvement récent" />}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Sous-composants ────────────────────────────────────────────

function SectionHeader({
  title, subtitle, badge, action, onAction,
}: {
  title: string; subtitle?: string; badge?: number; action?: string; onAction?: () => void;
}) {
  return (
    <View style={styles.sectionHeader}>
      <View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Text style={styles.sectionTitle}>{title}</Text>
          {badge != null && (
            <View style={styles.sectionBadge}>
              <Text style={styles.sectionBadgeText}>{badge}</Text>
            </View>
          )}
        </View>
        {subtitle && <Text style={styles.sectionSub}>{subtitle}</Text>}
      </View>
      {action && (
        <TouchableOpacity onPress={onAction}>
          <Text style={styles.sectionAction}>{action} ›</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

function KpiCard({
  label, value, unit, delta, up, color, iconName,
}: {
  label: string; value: string; unit: string;
  delta: string; up: boolean; color: string; iconName: any;
}) {
  return (
    <View style={styles.kpiCard}>
      <View style={styles.kpiTop}>
        <View style={[styles.kpiIcon, { backgroundColor: color + '1a' }]}>
          <Ionicons name={iconName} size={14} color={color} />
        </View>
        <View style={[styles.kpiDelta, { backgroundColor: up ? Colors.greenSoft : Colors.redSoft }]}>
          <Text style={[styles.kpiDeltaText, { color: up ? Colors.green : Colors.red }]}>{delta}</Text>
        </View>
      </View>
      <Text style={styles.kpiLabel}>{label}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 3, marginTop: 2 }}>
        <Text style={styles.kpiValue}>{value}</Text>
        {unit !== '' && <Text style={styles.kpiUnit}>{unit}</Text>}
      </View>
    </View>
  );
}

function StockRow({ stock }: { stock: any }) {
  const color  = STOCK_COLORS[stock.produit_sigle ?? ''] ?? Colors.navy;
  return (
    <View style={styles.stockCard}>
      <View style={[styles.stockBadge, { backgroundColor: color + '18', borderColor: color + '40' }]}>
        <Text style={[styles.stockSigle, { color }]}>{stock.produit_sigle}</Text>
      </View>
      <View style={styles.stockBody}>
        <Text style={styles.stockName} numberOfLines={1}>{stock.produit_nom}</Text>
        <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 4, marginTop: 2 }}>
          <Text style={styles.stockValue}>{fmtN(stock.stock_ambiant)}</Text>
          <Text style={styles.stockUnitLabel}>L · ambiant</Text>
        </View>
      </View>
    </View>
  );
}

function ActivityRow({ mvt }: { mvt: DernierMouvement }) {
  const meta    = TypeMeta[mvt.type] ?? { label: mvt.type, color: Colors.slate, soft: Colors.cloud, glyph: '·' };
  const date    = new Date(mvt.date);
  const hasTime = mvt.date?.includes('T');
  const time    = !hasTime || isNaN(date.getTime())
    ? ''
    : date.getHours().toString().padStart(2, '0') + ':' + date.getMinutes().toString().padStart(2, '0');

  return (
    <View style={styles.actRow}>
      <View style={[styles.actGlyph, { backgroundColor: meta.soft }]}>
        <Text style={[styles.actGlyphText, { color: meta.color }]}>{meta.glyph}</Text>
      </View>
      <View style={styles.actBody}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <Text style={[styles.actType, { color: meta.color }]}>{meta.label}</Text>
          <View style={styles.actDot} />
          <Text style={styles.actTime}>{time}</Text>
        </View>
        <Text style={styles.actProduit} numberOfLines={1}>{mvt.produit}</Text>
        {mvt.reference && (
          <Text style={styles.actDest} numberOfLines={1}>{mvt.reference}</Text>
        )}
      </View>
      <Text style={[styles.actQte, { color: meta.color }]}>
        {mvt.type === 'ENTREE' ? '+' : mvt.type === 'SORTIE' ? '−' : '·'} {fmtN(mvt.quantite_ambiant)}
      </Text>
    </View>
  );
}

function EmptyCard({ text }: { text: string }) {
  return (
    <View style={styles.emptyCard}>
      <Text style={styles.emptyText}>{text}</Text>
    </View>
  );
}

// couleurs par sigle (fallback si API ne les fournit pas)
const STOCK_COLORS: Record<string, string> = {
  GO:  Colors.orange,
  SP:  Colors.green,
  JET: Colors.cyan,
  PET: Colors.purple,
};

// ── Styles ─────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },

  // Hero
  hero: {
    paddingTop: 18,
    paddingHorizontal: 20,
    paddingBottom: 84,
    overflow: 'hidden',
    position: 'relative',
  },
  glow1: {
    position: 'absolute', top: -60, right: -40,
    width: 200, height: 200, borderRadius: 100,
    backgroundColor: Colors.orange + '33',
  },
  glow2: {
    position: 'absolute', bottom: 60, right: 30,
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: Colors.orange + '15',
  },
  heroTop: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 0,
  },
  heroLeft:    { flexDirection: 'row', alignItems: 'center', gap: 10 },
  avatar: {
    width: 38, height: 38, borderRadius: 12,
    backgroundColor: Colors.white + '26',
    borderWidth: 1, borderColor: Colors.white + '30',
    alignItems: 'center', justifyContent: 'center',
  },
  avatarText:  { color: Colors.white, fontWeight: '800', fontSize: 13 },
  heroGreet:   { color: Colors.white + 'b3', fontSize: 11 },
  heroName:    { color: Colors.white, fontWeight: '700', fontSize: 14, marginTop: 1 },
  heroActions: { flexDirection: 'row', gap: 8 },
  iconBtn: {
    width: 38, height: 38, borderRadius: 12,
    backgroundColor: Colors.white + '26',
    borderWidth: 1, borderColor: Colors.white + '30',
    alignItems: 'center', justifyContent: 'center',
    position: 'relative',
  },
  notifBadge: {
    position: 'absolute', top: 5, right: 5,
    minWidth: 16, height: 16, borderRadius: 8,
    backgroundColor: Colors.red,
    borderWidth: 2, borderColor: Colors.navyDeep,
    alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: 2,
  },
  notifBadgeText: {
    color: Colors.white,
    fontSize: 9,
    fontWeight: '800',
    lineHeight: 12,
  },
  depotPill: {
    marginTop: 18,
    flexDirection: 'row', alignItems: 'center', gap: 6,
    alignSelf: 'flex-start',
    paddingVertical: 5, paddingHorizontal: 10,
    backgroundColor: Colors.white + '1a',
    borderWidth: 1, borderColor: Colors.white + '22',
    borderRadius: Radius.pill,
  },
  depotDot: {
    width: 18, height: 18, borderRadius: 9,
    backgroundColor: Colors.orange,
    alignItems: 'center', justifyContent: 'center',
  },
  depotDotText: { color: Colors.white, fontSize: 9, fontWeight: '800' },
  depotText:    { color: Colors.white, fontSize: 11, fontWeight: '600', maxWidth: 220 },
  totalBlock:   { marginTop: 18 },
  totalLabel:   { color: Colors.white + 'a6', fontSize: 11, fontWeight: '600', letterSpacing: 0.4, textTransform: 'uppercase' },
  totalRow:     { flexDirection: 'row', alignItems: 'flex-end', gap: 6, marginTop: 6 },
  totalValue:   { color: Colors.white, fontSize: 38, fontWeight: '800', letterSpacing: -1 },
  totalUnit:    { color: Colors.white + 'e6', fontSize: 15, fontWeight: '700', marginBottom: 6 },
  totalDelta:   { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 },
  deltaChip: {
    flexDirection: 'row', alignItems: 'center', gap: 3,
    backgroundColor: '#7BE2A622',
    borderRadius: Radius.pill,
    paddingHorizontal: 7, paddingVertical: 3,
  },
  deltaText: { color: '#7BE2A6', fontSize: 11, fontWeight: '700' },
  deltaDate: { color: Colors.white + 'a6', fontSize: 11 },

  // KPI grid
  kpiWrap: {
    paddingHorizontal: 16,
    marginTop: -64,
    zIndex: 2,
  },
  kpiGrid: {
    flexDirection: 'row', flexWrap: 'wrap', gap: 10,
  },
  kpiCard: {
    flex: 1, minWidth: '46%',
    backgroundColor: Colors.white,
    borderRadius: Radius.lg, padding: 14,
    borderWidth: 1, borderColor: Colors.cloud,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 4, elevation: 2,
  },
  kpiTop:       { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  kpiIcon:      { width: 28, height: 28, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  kpiDelta:     { borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  kpiDeltaText: { fontSize: 10, fontWeight: '700' },
  kpiLabel:     { fontSize: 11, color: Colors.slate, fontWeight: '500' },
  kpiValue:     { fontSize: 20, fontWeight: '800', color: Colors.ink, letterSpacing: -0.5 },
  kpiUnit:      { fontSize: 11, color: Colors.slate, fontWeight: '600' },

  // Section header
  pad: { paddingHorizontal: 16, gap: 10 },
  sectionHeader: {
    paddingHorizontal: 20, paddingTop: 22, paddingBottom: 10,
    flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between',
  },
  sectionTitle:     { fontSize: 14, fontWeight: '800', color: Colors.ink, letterSpacing: -0.2 },
  sectionSub:       { fontSize: 11, color: Colors.slate, marginTop: 1 },
  sectionBadge: {
    backgroundColor: Colors.navy, borderRadius: 6,
    paddingHorizontal: 6, paddingVertical: 1,
  },
  sectionBadgeText: { color: Colors.white, fontSize: 10, fontWeight: '700' },
  sectionAction:    { fontSize: 12, fontWeight: '700', color: Colors.navy },

  // Stock rows
  stockCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg, padding: 14,
    borderWidth: 1, borderColor: Colors.cloud,
    flexDirection: 'row', alignItems: 'center', gap: 12,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  stockBadge: {
    width: 46, height: 46, borderRadius: 14,
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 1,
  },
  stockSigle:     { fontSize: 11, fontWeight: '800', fontVariant: ['tabular-nums'] },
  stockBody:      { flex: 1 },
  stockName:      { fontSize: 13, fontWeight: '700', color: Colors.ink },
  stockValue:     { fontSize: 16, fontWeight: '800', color: Colors.ink, letterSpacing: -0.3 },
  stockUnitLabel: { fontSize: 11, color: Colors.slate, fontWeight: '600' },

  // Gauges card
  gaugesCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg, padding: 16,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 4, elevation: 2,
  },
  gaugeRow:      {},
  gaugeHeader:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  gaugeTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  gaugeDot:      { width: 8, height: 8, borderRadius: 2 },
  gaugeName:     { fontSize: 12, fontWeight: '700', color: Colors.ink },
  gaugeSigle:    { fontSize: 10, color: Colors.slate },
  gaugePct:      { fontSize: 12, fontWeight: '700', color: Colors.ink },
  gaugeTrack: {
    height: 8, backgroundColor: Colors.cloud,
    borderRadius: Radius.pill, overflow: 'hidden',
  },
  gaugeFill:  { height: '100%', borderRadius: Radius.pill },
  gaugeMeta:  { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  gaugeMetaText: { fontSize: 10, color: Colors.slate },

  // Activity rows
  actRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    padding: 12,
    backgroundColor: Colors.white,
    borderWidth: 1, borderColor: Colors.cloud,
    borderRadius: Radius.md,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 2, elevation: 1,
  },
  actGlyph: {
    width: 38, height: 38, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
  },
  actGlyphText: { fontSize: 18, fontWeight: '800', lineHeight: 22 },
  actBody:      { flex: 1, minWidth: 0 },
  actType:      { fontSize: 10, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.5 },
  actDot:       { width: 3, height: 3, borderRadius: 1.5, backgroundColor: Colors.silver },
  actTime:      { fontSize: 10, color: Colors.slate },
  actProduit:   { fontSize: 13, fontWeight: '600', color: Colors.ink, marginTop: 2 },
  actDest:      { fontSize: 10, color: Colors.slate, marginTop: 1 },
  actQte:       { fontSize: 13, fontWeight: '800' },

  emptyCard: {
    backgroundColor: Colors.white, borderRadius: Radius.md,
    padding: Spacing.lg, alignItems: 'center',
  },
  emptyText: { color: Colors.slate, fontSize: FontSize.sm },
});
