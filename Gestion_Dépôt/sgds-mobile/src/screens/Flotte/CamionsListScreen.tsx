import React, { useState, useCallback, useMemo } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  TextInput, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { camionsApi, Camion } from '../../api/camions';
import { Colors, Radius } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';
import { useAuth } from '../../context/AuthContext';
import type { FlotteStackParams } from '../../navigation/AppNavigator';

type Nav = NativeStackNavigationProp<FlotteStackParams>;

const STATUT_META: Record<string, { label: string; color: string; soft: string }> = {
  EN_SERVICE:     { label: 'En service',    color: Colors.green, soft: Colors.greenSoft },
  HORS_SERVICE:   { label: 'Hors service',  color: Colors.red,   soft: Colors.redSoft },
  EN_MAINTENANCE: { label: 'Maintenance',   color: Colors.amber, soft: Colors.amberSoft },
  RETIRE:         { label: 'Retiré',        color: Colors.slate, soft: Colors.cloud },
};

const FILTER_CHIPS = [
  { key: '',              label: 'Tous' },
  { key: 'EN_SERVICE',    label: 'En service' },
  { key: 'HORS_SERVICE',  label: 'Hors service' },
  { key: 'EN_MAINTENANCE',label: 'Maintenance' },
];

export function CamionsListScreen() {
  const navigation = useNavigation<Nav>();
  const { user, refreshPermissions } = useAuth();
  const perms = user?.permissions ?? {};

  const [items, setItems]     = useState<Camion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);
  const [statut, setStatut]   = useState('');
  const [search, setSearch]   = useState('');

  useFocusEffect(useCallback(() => { refreshPermissions(); }, [refreshPermissions]));

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await camionsApi.list({ statut: statut || undefined });
      setItems(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [statut]);

  useFocusEffect(useCallback(() => { fetchData(); }, [fetchData]));

  const filtered = useMemo(() => {
    if (!search.trim()) return items;
    const q = search.toLowerCase();
    return items.filter(c =>
      c.immatriculation.toLowerCase().includes(q) ||
      c.marque.toLowerCase().includes(q)
    );
  }, [items, search]);

  if (!perms.voir_camion) {
    return <ErrorMessage message="Vous n'avez pas l'autorisation de consulter les camions." />;
  }
  if (loading) return <LoadingSpinner fullScreen message="Chargement des camions..." />;
  if (error)   return <ErrorMessage message={error} onRetry={fetchData} />;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="chevron-back" size={20} color={Colors.ink} />
          </TouchableOpacity>
          <View style={{ flex: 1 }}>
            <Text style={styles.headerSub}>Flotte</Text>
            <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 6 }}>
              <Text style={styles.headerCount}>{filtered.length}</Text>
              <Text style={styles.headerCountLabel}>camions</Text>
            </View>
          </View>
          {perms.ajouter_camion && (
            <TouchableOpacity style={styles.addBtn} onPress={() => navigation.navigate('CamionForm', {})}>
              <Ionicons name="add" size={20} color={Colors.white} />
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.searchRow}>
          <View style={styles.searchBox}>
            <Ionicons name="search-outline" size={16} color={Colors.slate} />
            <TextInput
              style={styles.searchInput}
              value={search}
              onChangeText={setSearch}
              placeholder="Immatriculation, marque…"
              placeholderTextColor={Colors.silver}
            />
            {search.length > 0 && (
              <TouchableOpacity onPress={() => setSearch('')}>
                <Ionicons name="close-circle" size={16} color={Colors.slate} />
              </TouchableOpacity>
            )}
          </View>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.chipsScroll}
          contentContainerStyle={styles.chipsContent}
        >
          {FILTER_CHIPS.map(chip => {
            const active = statut === chip.key;
            return (
              <TouchableOpacity
                key={chip.key}
                onPress={() => setStatut(chip.key)}
                style={[styles.chip, { backgroundColor: active ? Colors.navy : Colors.cloud }]}
                activeOpacity={0.7}
              >
                <Text style={[styles.chipText, { color: active ? Colors.white : Colors.graphite }]}>
                  {chip.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      <FlatList
        data={filtered}
        keyExtractor={item => String(item.id)}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <CamionCard camion={item} onPress={() => navigation.navigate('CamionDetail', { id: item.id })} />
        )}
        ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="car-outline" size={38} color={Colors.silver} />
            <Text style={styles.emptyText}>Aucun camion trouvé</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

function CamionCard({ camion, onPress }: { camion: Camion; onPress: () => void }) {
  const meta = STATUT_META[camion.statut] ?? { label: camion.statut, color: Colors.slate, soft: Colors.cloud };
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.cardIcon}>
        <Ionicons name="car" size={22} color={Colors.navy} />
      </View>
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={styles.cardTitle} numberOfLines={1}>{camion.immatriculation}</Text>
        <Text style={styles.cardSub} numberOfLines={1}>
          {camion.marque}{camion.modele ? ` · ${camion.modele}` : ''}
        </Text>
        <Text style={styles.cardMeta}>
          {Number(camion.capacite_totale).toLocaleString('fr-FR')} L · {camion.nombre_compartiments} compart.
        </Text>
      </View>
      <View style={[styles.statutBadge, { backgroundColor: meta.soft }]}>
        <Text style={[styles.statutText, { color: meta.color }]}>{meta.label}</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },

  header: {
    backgroundColor: Colors.white,
    paddingTop: 14,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  headerTop: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingHorizontal: 16, paddingBottom: 14,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: Colors.cloud,
    alignItems: 'center', justifyContent: 'center',
  },
  headerSub:        { fontSize: 11, color: Colors.slate, fontWeight: '600' },
  headerCount:      { fontSize: 20, fontWeight: '800', color: Colors.ink, letterSpacing: -0.4 },
  headerCountLabel: { fontSize: 13, color: Colors.slate, fontWeight: '600' },
  addBtn: {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: Colors.navy,
    alignItems: 'center', justifyContent: 'center',
  },

  searchRow: { paddingHorizontal: 20, marginBottom: 12 },
  searchBox: {
    height: 40, backgroundColor: Colors.cloud, borderRadius: 12,
    flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12,
  },
  searchInput: { flex: 1, fontSize: 13, color: Colors.ink },

  chipsScroll:  { maxHeight: 44 },
  chipsContent: { paddingHorizontal: 20, paddingBottom: 12, gap: 8, flexDirection: 'row' },
  chip: { paddingVertical: 7, paddingHorizontal: 12, borderRadius: 999 },
  chipText: { fontSize: 12, fontWeight: '700' },

  listContent: { padding: 16 },

  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg, padding: 12,
    borderWidth: 1, borderColor: Colors.cloud,
    flexDirection: 'row', alignItems: 'center', gap: 12,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  cardIcon: {
    width: 46, height: 46, borderRadius: 12,
    backgroundColor: Colors.navyTint,
    alignItems: 'center', justifyContent: 'center',
  },
  cardTitle: { fontSize: 14, fontWeight: '800', color: Colors.ink },
  cardSub:   { fontSize: 12, color: Colors.slate, marginTop: 1 },
  cardMeta:  { fontSize: 10, color: Colors.silver, marginTop: 2 },

  statutBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  statutText:  { fontSize: 9, fontWeight: '800' },

  empty: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyText: { fontSize: 13, color: Colors.slate },
});
