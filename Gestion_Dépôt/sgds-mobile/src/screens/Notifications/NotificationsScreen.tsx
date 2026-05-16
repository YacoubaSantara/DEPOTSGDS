import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { Colors, Spacing, FontSize, Radius } from '../../constants/colors';
import { notificationsApi, NotificationItem } from '../../api/notifications';
import type { TabParams } from '../../navigation/AppNavigator';

// ── Types navigation ────────────────────────────────────────────

type NavProp = BottomTabNavigationProp<TabParams, 'Notifications'>;

// ── Helpers ─────────────────────────────────────────────────────

const TYPE_META: Record<NotificationItem['type_notif'], { couleur: string; fond: string; glyph: string }> = {
  ENTREE:        { couleur: Colors.green,  fond: Colors.greenSoft,  glyph: '↓' },
  SORTIE:        { couleur: Colors.red,    fond: Colors.redSoft,    glyph: '↑' },
  CESSION_EMISE: { couleur: Colors.purple, fond: Colors.purpleSoft, glyph: '⇄' },
  CESSION_RECUE: { couleur: Colors.purple, fond: Colors.purpleSoft, glyph: '⇄' },
  ACQUITTEMENT:  { couleur: Colors.cyan,   fond: Colors.cyanSoft,   glyph: '✓' },
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "à l'instant";
  if (diffMin < 60) return `il y a ${diffMin} min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `il y a ${diffH} h`;
  const diffJ = Math.floor(diffH / 24);
  if (diffJ < 7) return `il y a ${diffJ} j`;
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// ── Composant item ──────────────────────────────────────────────

function NotifItem({
  item,
  onPress,
}: {
  item: NotificationItem;
  onPress: (item: NotificationItem) => void;
}) {
  const meta = TYPE_META[item.type_notif];
  return (
    <TouchableOpacity
      style={[styles.item, !item.lue && styles.itemNonLue]}
      activeOpacity={0.75}
      onPress={() => onPress(item)}
    >
      <View style={[styles.itemIcon, { backgroundColor: meta.fond }]}>
        <Text style={[styles.itemGlyph, { color: meta.couleur }]}>{meta.glyph}</Text>
      </View>
      <View style={styles.itemBody}>
        <View style={styles.itemTitreRow}>
          <Text style={styles.itemTitre} numberOfLines={1}>{item.titre}</Text>
          {!item.lue && <View style={[styles.dotNonLu, { backgroundColor: meta.couleur }]} />}
        </View>
        <Text style={styles.itemMessage} numberOfLines={3}>{item.message}</Text>
        <View style={styles.itemFooter}>
          <Text style={styles.itemDate}>{formatDate(item.date_creation)}</Text>
          {item.mouvement_id && (
            <Text style={styles.itemLinkHint}>Voir le mouvement ›</Text>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

// ── Écran principal ─────────────────────────────────────────────

export function NotificationsScreen() {
  const navigation = useNavigation<NavProp>();

  const [notifs, setNotifs]         = useState<NotificationItem[]>([]);
  const [nonLues, setNonLues]       = useState(0);
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [erreur, setErreur]         = useState<string | null>(null);

  const charger = useCallback(async (silent = false) => {
    if (!silent) setErreur(null);
    try {
      const res = await notificationsApi.getAll();
      setNotifs(res.data.results);
      setNonLues(res.data.count_non_lues);
      setErreur(null);
    } catch (e: any) {
      const msg =
        e?.response?.data?.detail ??
        e?.message ??
        'Impossible de charger les notifications.';
      setErreur(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      charger();
    }, [charger]),
  );

  const onRefresh = () => {
    setRefreshing(true);
    charger(true);
  };

  const handlePress = useCallback(
    async (item: NotificationItem) => {
      // Marquer comme lu (optimiste)
      if (!item.lue) {
        setNotifs((prev) => prev.map((n) => (n.id === item.id ? { ...n, lue: true } : n)));
        setNonLues((prev) => Math.max(0, prev - 1));
        notificationsApi.marquerLus([item.id]).catch(() => undefined);
      }
      // Naviguer vers le détail du mouvement si disponible
      if (item.mouvement_id) {
        (navigation as any).navigate('Mouvements', {
          screen: 'MouvementDetail',
          params: { id: item.mouvement_id },
        });
      }
    },
    [navigation],
  );

  const toutLire = async () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, lue: true })));
    setNonLues(0);
    notificationsApi.toutLire().catch(() => undefined);
  };

  // ── Rendu ───────────────────────────────────────────────────

  const renderHeader = () => (
    <View style={styles.header}>
      <Text style={styles.headerTitre}>
        Notifications{nonLues > 0 ? ` (${nonLues})` : ''}
      </Text>
      {nonLues > 0 && (
        <TouchableOpacity onPress={toutLire} activeOpacity={0.7}>
          <Text style={styles.toutLireBtn}>Tout marquer lu</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        {renderHeader()}
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.navy} />
        </View>
      </SafeAreaView>
    );
  }

  if (erreur) {
    return (
      <SafeAreaView style={styles.container}>
        {renderHeader()}
        <View style={styles.centered}>
          <Text style={styles.erreurIcon}>⚠️</Text>
          <Text style={styles.erreurMsg}>{erreur}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={() => { setLoading(true); charger(); }}>
            <Text style={styles.retryBtnText}>Réessayer</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {renderHeader()}
      <FlatList
        data={notifs}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <NotifItem item={item} onPress={handlePress} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>🔔</Text>
            <Text style={styles.emptyTitre}>Aucune notification</Text>
            <Text style={styles.emptySub}>
              Vous serez notifié lors de chaque mouvement vous concernant.
            </Text>
          </View>
        }
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={Colors.navy}
            colors={[Colors.navy]}
          />
        }
        contentContainerStyle={notifs.length === 0 ? styles.emptyContainer : undefined}
        ItemSeparatorComponent={() => <View style={styles.separateur} />}
      />
    </SafeAreaView>
  );
}

// ── Styles ──────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.paper,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm + 4,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.mist,
  },
  headerTitre: {
    fontSize: FontSize.lg,
    fontWeight: '700',
    color: Colors.ink,
  },
  toutLireBtn: {
    fontSize: FontSize.sm,
    fontWeight: '600',
    color: Colors.orange,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: Spacing.sm,
    paddingHorizontal: Spacing.xl,
  },
  erreurIcon: { fontSize: 36 },
  erreurMsg: {
    fontSize: FontSize.sm,
    color: Colors.red,
    textAlign: 'center',
    lineHeight: 20,
  },
  retryBtn: {
    marginTop: Spacing.xs,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs + 2,
    backgroundColor: Colors.navy,
    borderRadius: Radius.md,
  },
  retryBtnText: {
    color: Colors.white,
    fontWeight: '700',
    fontSize: FontSize.sm,
  },
  item: {
    flexDirection: 'row',
    gap: Spacing.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm + 4,
    backgroundColor: Colors.white,
  },
  itemNonLue: {
    backgroundColor: Colors.navyTint,
  },
  itemIcon: {
    width: 36,
    height: 36,
    borderRadius: Radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  itemGlyph: {
    fontSize: FontSize.md,
    fontWeight: '800',
  },
  itemBody: {
    flex: 1,
    gap: 2,
  },
  itemTitreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  itemTitre: {
    flex: 1,
    fontSize: FontSize.sm,
    fontWeight: '700',
    color: Colors.ink,
  },
  dotNonLu: {
    width: 8,
    height: 8,
    borderRadius: 4,
    flexShrink: 0,
  },
  itemMessage: {
    fontSize: FontSize.xs + 1,
    color: Colors.graphite,
    lineHeight: 18,
  },
  itemFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  itemDate: {
    fontSize: FontSize.xs,
    color: Colors.slate,
  },
  itemLinkHint: {
    fontSize: FontSize.xs,
    color: Colors.navy,
    fontWeight: '600',
  },
  separateur: {
    height: 1,
    backgroundColor: Colors.mist,
    marginLeft: Spacing.md + 36 + Spacing.sm,
  },
  emptyContainer: {
    flexGrow: 1,
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.xl,
    gap: Spacing.sm,
    paddingTop: 80,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: Spacing.sm,
  },
  emptyTitre: {
    fontSize: FontSize.lg,
    fontWeight: '700',
    color: Colors.ink,
    textAlign: 'center',
  },
  emptySub: {
    fontSize: FontSize.sm,
    color: Colors.slate,
    textAlign: 'center',
    lineHeight: 20,
  },
});
