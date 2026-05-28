import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  Pressable,
  RefreshControl,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { Colors, Spacing, FontSize, Radius } from '../../constants/colors';
import { notificationsApi, NotificationItem } from '../../api/notifications';
import type { TabParams } from '../../navigation/AppNavigator';

type NavProp = BottomTabNavigationProp<TabParams, 'Notifications'>;
type Filter = 'all' | 'unread';

// ── Design tokens locaux ───────────────────────────────────────────────────

const TYPE_META: Record<NotificationItem['type_notif'], {
  color: string;
  bg: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
}> = {
  ENTREE:                   { color: Colors.green,  bg: Colors.greenSoft,  icon: 'arrow-down-circle-outline',  label: 'Entrée' },
  SORTIE:                   { color: Colors.red,    bg: Colors.redSoft,    icon: 'arrow-up-circle-outline',    label: 'Sortie' },
  CESSION_EMISE:            { color: Colors.purple, bg: Colors.purpleSoft, icon: 'swap-horizontal-outline',    label: 'Cession émise' },
  CESSION_RECUE:            { color: Colors.purple, bg: Colors.purpleSoft, icon: 'swap-horizontal-outline',    label: 'Cession reçue' },
  ACQUITTEMENT:             { color: Colors.cyan,   bg: Colors.cyanSoft,   icon: 'checkmark-circle-outline',   label: 'Acquittement' },
  DOCUMENT_AJOUTE:          { color: Colors.orange, bg: Colors.orangeSoft, icon: 'document-attach-outline',    label: 'Document ajouté' },
  ETAT_MENSUEL_DISPONIBLE:  { color: Colors.amber,  bg: Colors.amberSoft,  icon: 'bar-chart-outline',          label: 'État mensuel' },
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMin = Math.floor((now.getTime() - d.getTime()) / 60000);
  if (diffMin < 1)  return "à l'instant";
  if (diffMin < 60) return `il y a ${diffMin} min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24)   return `il y a ${diffH}h`;
  const diffJ = Math.floor(diffH / 24);
  if (diffJ < 7)    return `il y a ${diffJ}j`;
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function SkeletonScreen() {
  const opacity = useRef(new Animated.Value(0.35)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 0.9, duration: 700, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.35, duration: 700, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [opacity]);

  const Block = ({ w, h, r = 6 }: { w: number | string; h: number; r?: number }) => (
    <Animated.View style={{ width: w as any, height: h, borderRadius: r, backgroundColor: Colors.mist, opacity }} />
  );

  return (
    <View style={styles.skeletonContainer}>
      {[1, 2, 3, 4, 5].map(i => (
        <View key={i} style={styles.skeletonItem}>
          <Block w={44} h={44} r={Radius.sm} />
          <View style={styles.skeletonBody}>
            <Block w={i % 2 === 0 ? '70%' : '55%'} h={12} />
            <View style={{ height: 6 }} />
            <Block w="90%" h={10} />
            <View style={{ height: 4 }} />
            <Block w="75%" h={10} />
            <View style={{ height: 8 }} />
            <Block w="35%" h={9} />
          </View>
        </View>
      ))}
    </View>
  );
}

// ── Tabs ───────────────────────────────────────────────────────────────────

function FilterTabs({
  active,
  onChange,
  total,
  unread,
}: {
  active: Filter;
  onChange: (f: Filter) => void;
  total: number;
  unread: number;
}) {
  return (
    <View style={styles.tabs}>
      {(['all', 'unread'] as Filter[]).map(f => {
        const isActive = active === f;
        const count = f === 'all' ? total : unread;
        return (
          <Pressable
            key={f}
            style={[styles.tab, isActive && styles.tabActive]}
            onPress={() => onChange(f)}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
          >
            <Text style={[styles.tabText, isActive && styles.tabTextActive]}>
              {f === 'all' ? 'Toutes' : 'Non lues'}
            </Text>
            {count > 0 && (
              <View style={[
                styles.tabChip,
                isActive && styles.tabChipActive,
                f === 'unread' && styles.tabChipAlert,
                f === 'unread' && isActive && styles.tabChipAlertActive,
              ]}>
                <Text style={[
                  styles.tabChipText,
                  isActive && styles.tabChipTextActive,
                  f === 'unread' && styles.tabChipAlertText,
                ]}>
                  {count > 99 ? '99+' : count}
                </Text>
              </View>
            )}
          </Pressable>
        );
      })}
    </View>
  );
}

// ── Notification item ──────────────────────────────────────────────────────

function NotifItem({
  item,
  onPress,
}: {
  item: NotificationItem;
  onPress: (item: NotificationItem) => void;
}) {
  const meta = TYPE_META[item.type_notif];
  return (
    <Pressable
      style={({ pressed }) => [
        styles.item,
        !item.lue && styles.itemUnread,
        pressed && styles.itemPressed,
      ]}
      onPress={() => onPress(item)}
      accessibilityRole="button"
      accessibilityLabel={`${meta.label} : ${item.titre}. ${item.lue ? 'Lue' : 'Non lue'}`}
    >
      {/* Barre colorée gauche pour non-lue */}
      {!item.lue && <View style={[styles.unreadBar, { backgroundColor: meta.color }]} />}

      {/* Icône */}
      <View style={[styles.iconWrap, { backgroundColor: meta.bg }]}>
        <Ionicons name={meta.icon} size={22} color={meta.color} />
      </View>

      {/* Contenu */}
      <View style={styles.body}>
        <View style={styles.titleRow}>
          <Text
            style={[styles.title, !item.lue && styles.titleUnread]}
            numberOfLines={1}
          >
            {item.titre}
          </Text>
          {!item.lue && <View style={[styles.dot, { backgroundColor: meta.color }]} />}
        </View>

        <Text style={styles.msg} numberOfLines={2}>{item.message}</Text>

        <View style={styles.footerRow}>
          <View style={styles.dateWrap}>
            <Ionicons name="time-outline" size={11} color={Colors.slate} />
            <Text style={styles.date}>{formatDate(item.date_creation)}</Text>
          </View>
          {item.mouvement_id ? (
            <View style={styles.linkWrap}>
              <Text style={styles.linkText}>Voir le mouvement</Text>
              <Ionicons name="chevron-forward" size={11} color={Colors.navy} />
            </View>
          ) : item.lien ? (
            <View style={styles.linkWrap}>
              <Text style={styles.linkText}>Voir le rapport</Text>
              <Ionicons name="chevron-forward" size={11} color={Colors.amber} />
            </View>
          ) : null}
        </View>
      </View>
    </Pressable>
  );
}

// ── État vide ──────────────────────────────────────────────────────────────

function EmptyState({ isFiltered }: { isFiltered: boolean }) {
  return (
    <View style={styles.empty}>
      <View style={styles.emptyIconWrap}>
        <Ionicons
          name={isFiltered ? 'checkmark-circle-outline' : 'notifications-outline'}
          size={36}
          color={Colors.slate}
        />
      </View>
      <Text style={styles.emptyTitle}>
        {isFiltered ? 'Tout est à jour !' : 'Aucune notification'}
      </Text>
      <Text style={styles.emptySub}>
        {isFiltered
          ? 'Vous n\'avez aucune notification non lue.'
          : 'Vous serez notifié lors de chaque mouvement vous concernant.'}
      </Text>
    </View>
  );
}

// ── État d'erreur ──────────────────────────────────────────────────────────

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={styles.empty}>
      <View style={[styles.emptyIconWrap, styles.errorIconWrap]}>
        <Ionicons name="alert-circle-outline" size={36} color={Colors.red} />
      </View>
      <Text style={[styles.emptyTitle, { color: Colors.red }]}>Erreur de chargement</Text>
      <Text style={styles.emptySub}>{message}</Text>
      <Pressable style={styles.retryBtn} onPress={onRetry}>
        <Ionicons name="refresh-outline" size={14} color={Colors.white} />
        <Text style={styles.retryBtnText}>Réessayer</Text>
      </Pressable>
    </View>
  );
}

// ── Écran principal ────────────────────────────────────────────────────────

export function NotificationsScreen() {
  const navigation = useNavigation<NavProp>();

  const [notifs, setNotifs]         = useState<NotificationItem[]>([]);
  const [nonLues, setNonLues]       = useState(0);
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [erreur, setErreur]         = useState<string | null>(null);
  const [filter, setFilter]         = useState<Filter>('all');

  const charger = useCallback(async (silent = false) => {
    if (!silent) setErreur(null);
    try {
      const res = await notificationsApi.getAll();
      setNotifs(res.data.results);
      setNonLues(res.data.count_non_lues);
      setErreur(null);
    } catch (e: any) {
      setErreur(
        e?.response?.data?.detail ?? e?.message ?? 'Impossible de charger les notifications.'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      charger();
    }, [charger])
  );

  const onRefresh = () => {
    setRefreshing(true);
    charger(true);
  };

  const handlePress = useCallback(
    async (item: NotificationItem) => {
      if (!item.lue) {
        setNotifs(prev => prev.map(n => n.id === item.id ? { ...n, lue: true } : n));
        setNonLues(prev => Math.max(0, prev - 1));
        notificationsApi.marquerLus([item.id]).catch(() => undefined);
      }
      if (item.mouvement_id) {
        (navigation as any).navigate('Mouvements', {
          screen: 'MouvementDetail',
          params: { id: item.mouvement_id },
        });
      }
    },
    [navigation]
  );

  const toutLire = () => {
    setNotifs(prev => prev.map(n => ({ ...n, lue: true })));
    setNonLues(0);
    notificationsApi.toutLire().catch(() => undefined);
  };

  const filtered = filter === 'unread' ? notifs.filter(n => !n.lue) : notifs;

  // ── Rendu ──────────────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.container} edges={['top']}>

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Notifications</Text>
          {nonLues > 0 && (
            <Text style={styles.headerSub}>
              {nonLues} non lue{nonLues > 1 ? 's' : ''}
            </Text>
          )}
        </View>
        {nonLues > 0 && (
          <Pressable style={styles.toutLireBtn} onPress={toutLire}>
            <Ionicons name="checkmark-done-outline" size={14} color={Colors.navy} />
            <Text style={styles.toutLireText}>Tout marquer lu</Text>
          </Pressable>
        )}
      </View>

      {/* Tabs */}
      {!loading && !erreur && (
        <FilterTabs
          active={filter}
          onChange={setFilter}
          total={notifs.length}
          unread={nonLues}
        />
      )}

      {/* Contenu */}
      {loading ? (
        <SkeletonScreen />
      ) : erreur ? (
        <ErrorState
          message={erreur}
          onRetry={() => { setLoading(true); charger(); }}
        />
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={item => String(item.id)}
          renderItem={({ item }) => <NotifItem item={item} onPress={handlePress} />}
          ListEmptyComponent={<EmptyState isFiltered={filter === 'unread'} />}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={Colors.navy}
              colors={[Colors.navy]}
            />
          }
          contentContainerStyle={filtered.length === 0 ? styles.emptyContainer : styles.listPadding}
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaView>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.paper,
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.sm,
    paddingBottom: Spacing.sm,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.mist,
  },
  headerTitle: {
    fontSize: FontSize.xl,
    fontWeight: '800',
    color: Colors.ink,
    letterSpacing: -0.4,
  },
  headerSub: {
    fontSize: FontSize.xs,
    color: Colors.slate,
    marginTop: 2,
  },
  toutLireBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: Spacing.sm + 2,
    paddingVertical: 7,
    backgroundColor: Colors.navyTint,
    borderRadius: Radius.pill,
  },
  toutLireText: {
    fontSize: FontSize.xs,
    fontWeight: '700',
    color: Colors.navy,
  },

  // Tabs
  tabs: {
    flexDirection: 'row',
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.mist,
    paddingHorizontal: Spacing.md,
    gap: Spacing.xs,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 4,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: Colors.navy,
  },
  tabText: {
    fontSize: FontSize.sm,
    fontWeight: '600',
    color: Colors.slate,
  },
  tabTextActive: {
    color: Colors.navy,
    fontWeight: '700',
  },
  tabChip: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: Radius.pill,
    backgroundColor: Colors.cloud,
  },
  tabChipActive: {
    backgroundColor: Colors.navyTint,
  },
  tabChipAlert: {
    backgroundColor: Colors.redSoft,
  },
  tabChipAlertActive: {
    backgroundColor: Colors.redSoft,
  },
  tabChipText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.slate,
  },
  tabChipTextActive: {
    color: Colors.navy,
  },
  tabChipAlertText: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.red,
  },

  // Liste
  listPadding: {
    paddingBottom: Spacing.xl,
  },

  // Notification item
  item: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm + 2,
    paddingHorizontal: Spacing.md,
    paddingVertical: 14,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.mist,
    position: 'relative',
  },
  itemUnread: {
    backgroundColor: Colors.navyTint + '60',
  },
  itemPressed: {
    backgroundColor: Colors.cloud,
  },
  unreadBar: {
    position: 'absolute',
    left: 0,
    top: 12,
    bottom: 12,
    width: 3,
    borderTopRightRadius: 3,
    borderBottomRightRadius: 3,
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: Radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  body: {
    flex: 1,
    gap: 3,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  title: {
    flex: 1,
    fontSize: FontSize.sm,
    fontWeight: '600',
    color: Colors.graphite,
    lineHeight: 18,
  },
  titleUnread: {
    fontWeight: '800',
    color: Colors.ink,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    flexShrink: 0,
  },
  msg: {
    fontSize: FontSize.xs + 1,
    color: Colors.slate,
    lineHeight: 17,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 2,
  },
  dateWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  date: {
    fontSize: FontSize.xs,
    color: Colors.slate,
  },
  linkWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  linkText: {
    fontSize: FontSize.xs,
    fontWeight: '700',
    color: Colors.navy,
  },

  // Skeleton
  skeletonContainer: {
    backgroundColor: Colors.white,
  },
  skeletonItem: {
    flexDirection: 'row',
    gap: Spacing.sm + 2,
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.mist,
  },
  skeletonBody: {
    flex: 1,
    gap: 0,
  },

  // Empty / Error
  emptyContainer: {
    flexGrow: 1,
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.xl,
    paddingTop: 80,
    gap: Spacing.sm,
  },
  emptyIconWrap: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: Colors.cloud,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  errorIconWrap: {
    backgroundColor: Colors.redSoft,
  },
  emptyTitle: {
    fontSize: FontSize.lg,
    fontWeight: '800',
    color: Colors.ink,
    textAlign: 'center',
  },
  emptySub: {
    fontSize: FontSize.sm,
    color: Colors.slate,
    textAlign: 'center',
    lineHeight: 20,
    maxWidth: 280,
  },
  retryBtn: {
    marginTop: Spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: Spacing.md + 4,
    paddingVertical: 10,
    backgroundColor: Colors.navy,
    borderRadius: Radius.md,
  },
  retryBtnText: {
    color: Colors.white,
    fontWeight: '700',
    fontSize: FontSize.sm,
  },
});
