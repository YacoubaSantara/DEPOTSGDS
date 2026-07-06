import React, { useState, useCallback, useMemo } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  TextInput, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { chauffeursApi, Chauffeur } from '../../api/chauffeurs';
import { Colors, Radius } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';
import { useAuth } from '../../context/AuthContext';
import type { FlotteStackParams } from '../../navigation/AppNavigator';

type Nav = NativeStackNavigationProp<FlotteStackParams>;

const STATUT_META: Record<string, { label: string; color: string; soft: string }> = {
  ACTIF:    { label: 'Actif',    color: Colors.green, soft: Colors.greenSoft },
  INACTIF:  { label: 'Inactif',  color: Colors.slate, soft: Colors.cloud },
  SUSPENDU: { label: 'Suspendu', color: Colors.red,   soft: Colors.redSoft },
};

const FILTER_CHIPS = [
  { key: '',         label: 'Tous' },
  { key: 'ACTIF',    label: 'Actifs' },
  { key: 'INACTIF',  label: 'Inactifs' },
  { key: 'SUSPENDU', label: 'Suspendus' },
];

export function ChauffeursListScreen() {
  const navigation = useNavigation<Nav>();
  const { user, refreshPermissions } = useAuth();
  const perms = user?.permissions ?? {};

  const [items, setItems]     = useState<Chauffeur[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);
  const [statut, setStatut]   = useState('');
  const [search, setSearch]   = useState('');

  useFocusEffect(useCallback(() => { refreshPermissions(); }, [refreshPermissions]));

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await chauffeursApi.list({ statut: statut || undefined });
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
      c.nom.toLowerCase().includes(q) ||
      c.prenom.toLowerCase().includes(q) ||
      c.numero_permis.toLowerCase().includes(q)
    );
  }, [items, search]);

  if (!perms.voir_chauffeur) {
    return <ErrorMessage message="Vous n'avez pas l'autorisation de consulter les chauffeurs." />;
  }
  if (loading) return <LoadingSpinner fullScreen message="Chargement des chauffeurs..." />;
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
              <Text style={styles.headerCountLabel}>chauffeurs</Text>
            </View>
          </View>
          {perms.ajouter_chauffeur && (
            <TouchableOpacity style={styles.addBtn} onPress={() => navigation.navigate('ChauffeurForm', {})}>
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
              placeholder="Nom, prénom, permis…"
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
          <ChauffeurCard chauffeur={item} onPress={() => navigation.navigate('ChauffeurDetail', { id: item.id })} />
        )}
        ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="person-outline" size={38} color={Colors.silver} />
            <Text style={styles.emptyText}>Aucun chauffeur trouvé</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

function ChauffeurCard({ chauffeur, onPress }: { chauffeur: Chauffeur; onPress: () => void }) {
  const meta = STATUT_META[chauffeur.statut] ?? { label: chauffeur.statut, color: Colors.slate, soft: Colors.cloud };
  const initials = `${chauffeur.prenom[0] ?? ''}${chauffeur.nom[0] ?? ''}`.toUpperCase();
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{initials}</Text>
      </View>
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={styles.cardTitle} numberOfLines={1}>{chauffeur.prenom} {chauffeur.nom}</Text>
        <Text style={styles.cardSub} numberOfLines={1}>{chauffeur.telephone}</Text>
        {chauffeur.camion_immatriculation && (
          <View style={styles.camionRow}>
            <Ionicons name="car-outline" size={11} color={Colors.silver} />
            <Text style={styles.cardMeta}>{chauffeur.camion_immatriculation}</Text>
          </View>
        )}
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
  avatar: {
    width: 46, height: 46, borderRadius: 23,
    backgroundColor: Colors.orangeSoft,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarText: { fontSize: 14, fontWeight: '800', color: Colors.orangeDeep },
  cardTitle: { fontSize: 14, fontWeight: '800', color: Colors.ink },
  cardSub:   { fontSize: 12, color: Colors.slate, marginTop: 1 },
  camionRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 3 },
  cardMeta:  { fontSize: 10, color: Colors.silver },

  statutBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  statutText:  { fontSize: 9, fontWeight: '800' },

  empty: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyText: { fontSize: 13, color: Colors.slate },
});
