import React, { useState, useCallback, useMemo } from 'react';
import {
  View, Text, SectionList, TouchableOpacity, StyleSheet,
  TextInput, ScrollView, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { mouvementsApi, MouvementListItem, MouvementFilters } from '../../api/mouvements';
import { Colors, Radius, Spacing, FontSize, TypeMeta } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';
import type { MouvementsStackParams } from '../../navigation/AppNavigator';

type Nav = NativeStackNavigationProp<MouvementsStackParams>;

const FILTER_CHIPS = [
  { key: '',            label: 'Tous',     color: Colors.navy },
  { key: 'ENTREE',      label: 'Entrées',  color: Colors.entree },
  { key: 'SORTIE',      label: 'Sorties',  color: Colors.sortie },
  { key: 'CESSION',     label: 'Cessions', color: Colors.cession },
  { key: 'ACQUITTEMENT',label: 'Acquitt.', color: Colors.acquittement },
];

function fmtN(n: any): string {
  const v = Number(n);
  if (isNaN(v)) return '0';
  return v.toLocaleString('fr-FR', { maximumFractionDigits: 0 });
}

export function MouvementsScreen() {
  const navigation = useNavigation<Nav>();

  const [items, setItems]             = useState<MouvementListItem[]>([]);
  const [loading, setLoading]         = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError]             = useState<string | null>(null);
  const [page, setPage]               = useState(1);
  const [totalPages, setTotalPages]   = useState(1);
  const [total, setTotal]             = useState(0);
  const [filterType, setFilterType]   = useState('');
  const [search, setSearch]           = useState('');

  const fetchData = useCallback(async (p: number, type: string, reset = false) => {
    if (p === 1) setLoading(true); else setLoadingMore(true);
    setError(null);
    const filters: MouvementFilters = { page: p };
    if (type) filters.type = type;
    try {
      const res  = await mouvementsApi.list(filters);
      const data = res.data;
      setTotal(data.count);
      setTotalPages(data.total_pages);
      setItems(prev => (p === 1 || reset ? data.results : [...prev, ...data.results]));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useFocusEffect(useCallback(() => {
    setPage(1);
    fetchData(1, filterType, true);
  }, [fetchData, filterType]));

  const loadMore = () => {
    if (!loadingMore && page < totalPages) {
      const next = page + 1;
      setPage(next);
      fetchData(next, filterType);
    }
  };

  // Filtrage local par search
  const filtered = useMemo(() => {
    if (!search.trim()) return items;
    const q = search.toLowerCase();
    return items.filter(m =>
      m.produit?.toLowerCase().includes(q) ||
      m.reference?.toLowerCase().includes(q)
    );
  }, [items, search]);

  // Grouper par date
  const sections = useMemo(() => {
    const groups: Record<string, MouvementListItem[]> = {};
    filtered.forEach(m => {
      const d = m.date?.slice(0, 10) ?? 'inconnu';
      if (!groups[d]) groups[d] = [];
      groups[d].push(m);
    });
    return Object.keys(groups)
      .sort()
      .reverse()
      .map(d => ({ title: d, data: groups[d] }));
  }, [filtered]);

  const dayLabel = (key: string) => {
    const today = new Date().toISOString().slice(0, 10);
    const yest  = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    if (key === today) return "Aujourd'hui";
    if (key === yest)  return 'Hier';
    const d = new Date(key);
    return isNaN(d.getTime())
      ? key
      : d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
  };

  if (loading) return <LoadingSpinner fullScreen message="Chargement des mouvements..." />;
  if (error)   return <ErrorMessage message={error} onRetry={() => fetchData(1, filterType, true)} />;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* ── EN-TÊTE ──────────────────────────────────────── */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.headerSub}>Mouvements</Text>
            <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 6 }}>
              <Text style={styles.headerCount}>{filtered.length}</Text>
              <Text style={styles.headerCountLabel}>opérations</Text>
            </View>
          </View>
          <TouchableOpacity style={styles.addBtn}>
            <Ionicons name="add" size={18} color={Colors.white} />
          </TouchableOpacity>
        </View>

        {/* Recherche */}
        <View style={styles.searchRow}>
          <View style={styles.searchBox}>
            <Ionicons name="search-outline" size={16} color={Colors.slate} />
            <TextInput
              style={styles.searchInput}
              value={search}
              onChangeText={setSearch}
              placeholder="Référence, produit…"
              placeholderTextColor={Colors.silver}
            />
            {search.length > 0 && (
              <TouchableOpacity onPress={() => setSearch('')}>
                <Ionicons name="close-circle" size={16} color={Colors.slate} />
              </TouchableOpacity>
            )}
          </View>
          <TouchableOpacity
            style={[styles.filterIconBtn, filterType && styles.filterIconBtnActive]}
          >
            <Ionicons
              name="options-outline"
              size={16}
              color={filterType ? Colors.white : Colors.ink}
            />
          </TouchableOpacity>
        </View>

        {/* Chips */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.chipsScroll}
          contentContainerStyle={styles.chipsContent}
        >
          {FILTER_CHIPS.map(chip => {
            const active = filterType === chip.key;
            return (
              <TouchableOpacity
                key={chip.key}
                onPress={() => setFilterType(chip.key)}
                style={[
                  styles.chip,
                  { backgroundColor: active ? chip.color : Colors.cloud },
                ]}
                activeOpacity={0.7}
              >
                {chip.key !== '' && (
                  <View style={[
                    styles.chipDot,
                    { backgroundColor: active ? Colors.white : chip.color },
                  ]} />
                )}
                <Text style={[styles.chipText, { color: active ? Colors.white : Colors.graphite }]}>
                  {chip.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* ── LISTE ────────────────────────────────────────── */}
      <SectionList
        sections={sections}
        keyExtractor={item => String(item.id)}
        contentContainerStyle={styles.listContent}
        onEndReached={loadMore}
        onEndReachedThreshold={0.3}
        renderSectionHeader={({ section }) => (
          <View style={styles.groupHeader}>
            <View style={styles.groupDot} />
            <Text style={styles.groupLabel}>{dayLabel(section.title)}</Text>
            <View style={styles.groupLine} />
            <Text style={styles.groupCount}>{section.data.length} mvt</Text>
          </View>
        )}
        renderItem={({ item }) => (
          <MvtCard
            mvt={item}
            onPress={() => navigation.navigate('MouvementDetail', { id: item.id })}
          />
        )}
        ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        SectionSeparatorComponent={() => <View style={{ height: 0 }} />}
        ListFooterComponent={loadingMore
          ? <ActivityIndicator color={Colors.navy} style={{ padding: Spacing.lg }} />
          : <View style={{ height: 100 }} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>🔍</Text>
            <Text style={styles.emptyText}>Aucun mouvement trouvé</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

// ── MvtCard ────────────────────────────────────────────────────
function MvtCard({ mvt, onPress }: { mvt: MouvementListItem; onPress: () => void }) {
  const meta = TypeMeta[mvt.type] ?? {
    label: mvt.type, color: Colors.slate, soft: Colors.cloud, glyph: '·',
  };
  const date = new Date(mvt.date ?? '');
  const time = isNaN(date.getTime())
    ? ''
    : date.getHours().toString().padStart(2, '0') + ':' + date.getMinutes().toString().padStart(2, '0');

  return (
    <TouchableOpacity style={styles.mvtCard} onPress={onPress} activeOpacity={0.7}>
      {/* Ligne 1: badge type + ref + heure */}
      <View style={styles.mvtLine1}>
        <View style={styles.mvtLeft}>
          <View style={[styles.typeBadge, { backgroundColor: meta.soft }]}>
            <Text style={[styles.typeGlyph, { color: meta.color }]}>{meta.glyph}</Text>
            <Text style={[styles.typeLabel, { color: meta.color }]}>{meta.label}</Text>
          </View>
          <Text style={styles.mvtRef} numberOfLines={1}>{mvt.reference}</Text>
        </View>
        <Text style={styles.mvtTime}>{time}</Text>
      </View>

      {/* Ligne 2: produit + quantité */}
      <View style={styles.mvtLine2}>
        <View style={{ flex: 1, minWidth: 0 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <View style={styles.sigleBadge}>
              <Text style={styles.sigleText}>{mvt.produit_sigle}</Text>
            </View>
            <Text style={styles.mvtProduit} numberOfLines={1}>{mvt.produit}</Text>
          </View>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text style={[styles.mvtQte, { color: meta.color }]}>
            {(mvt as any).quantite_ambiant != null
              ? (mvt as any).quantite_ambiant.toLocaleString('fr-FR', { maximumFractionDigits: 0 })
              : '—'}
          </Text>
          <Text style={styles.mvtQteUnit}>LITRES · AMB</Text>
        </View>
      </View>

      {/* Ligne 3: logistique (si dispo) */}
      {(mvt as any).camion_immatriculation && (
        <View style={styles.mvtLogistic}>
          <Ionicons name="car-outline" size={12} color={Colors.silver} />
          <Text style={styles.mvtLogisticText}>{(mvt as any).camion_immatriculation}</Text>
          {(mvt as any).chauffeur_nom && (
            <>
              <View style={styles.logDot} />
              <Text style={styles.mvtLogisticText}>{(mvt as any).chauffeur_nom}</Text>
            </>
          )}
        </View>
      )}
    </TouchableOpacity>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe:  { flex: 1, backgroundColor: Colors.paper },

  // Header
  header: {
    backgroundColor: Colors.white,
    paddingTop: 14, paddingBottom: 0,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  headerTop: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20, paddingBottom: 14,
  },
  headerSub:        { fontSize: 11, color: Colors.slate, fontWeight: '600' },
  headerCount:      { fontSize: 22, fontWeight: '800', color: Colors.ink, letterSpacing: -0.4 },
  headerCountLabel: { fontSize: 13, color: Colors.slate, fontWeight: '600' },
  addBtn: {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: Colors.navy,
    alignItems: 'center', justifyContent: 'center',
  },

  // Recherche
  searchRow: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingHorizontal: 20, marginBottom: 12,
  },
  searchBox: {
    flex: 1, height: 40, backgroundColor: Colors.cloud, borderRadius: 12,
    flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12,
  },
  searchInput: { flex: 1, fontSize: 13, color: Colors.ink },
  filterIconBtn: {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: Colors.cloud,
    alignItems: 'center', justifyContent: 'center',
  },
  filterIconBtnActive: { backgroundColor: Colors.navy },

  // Chips
  chipsScroll:   { maxHeight: 44 },
  chipsContent:  { paddingHorizontal: 20, paddingBottom: 12, gap: 8, flexDirection: 'row' },
  chip: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingVertical: 7, paddingHorizontal: 12,
    borderRadius: Radius.pill,
  },
  chipDot:  { width: 6, height: 6, borderRadius: 3 },
  chipText: { fontSize: 12, fontWeight: '700' },

  // Liste
  listContent: { paddingTop: 12, paddingHorizontal: 16 },

  // Group header
  groupHeader: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    marginBottom: 8, marginTop: 18, paddingHorizontal: 4,
  },
  groupDot:   { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.orange },
  groupLabel: {
    fontSize: 11, fontWeight: '700', color: Colors.graphite,
    textTransform: 'capitalize', letterSpacing: 0.2,
  },
  groupLine:  { flex: 1, height: 1, backgroundColor: Colors.cloud },
  groupCount: { fontSize: 10, color: Colors.slate },

  // MvtCard
  mvtCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg, padding: 12,
    borderWidth: 1, borderColor: Colors.cloud,
    gap: 10,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  mvtLine1: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', gap: 10,
  },
  mvtLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  typeBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 5,
    paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 6,
  },
  typeGlyph: { fontSize: 10, fontWeight: '800' },
  typeLabel: { fontSize: 10, fontWeight: '800', letterSpacing: 0.5, textTransform: 'uppercase' },
  mvtRef:    { fontSize: 10, color: Colors.slate, maxWidth: 120 },
  mvtTime:   { fontSize: 10, color: Colors.slate },

  mvtLine2: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12,
  },
  sigleBadge: {
    backgroundColor: Colors.cloud, borderRadius: 4,
    paddingHorizontal: 5, paddingVertical: 1,
  },
  sigleText: { fontSize: 9, fontWeight: '800', color: Colors.graphite },
  mvtProduit: { fontSize: 14, fontWeight: '700', color: Colors.ink },
  mvtQte:     { fontSize: 16, fontWeight: '800', letterSpacing: -0.3 },
  mvtQteUnit: { fontSize: 9, color: Colors.slate, fontWeight: '600', letterSpacing: 0.5, marginTop: 1 },

  mvtLogistic: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingTop: 8,
    borderTopWidth: 1, borderTopColor: Colors.mist,
    borderStyle: 'dashed',
  },
  mvtLogisticText: { fontSize: 10, color: Colors.slate },
  logDot: { width: 3, height: 3, borderRadius: 1.5, backgroundColor: Colors.mist },

  // Empty
  empty: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyIcon: { fontSize: 38 },
  emptyText: { fontSize: FontSize.md, color: Colors.slate },
});
