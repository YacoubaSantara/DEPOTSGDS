import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as SecureStore from '../../utils/secureStorage';
import * as LocalAuthentication from 'expo-local-authentication';

import { profilApi, ProfilData } from '../../api/profil';
import { STORAGE_KEYS } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Colors, Radius, FontSize, TypeMeta } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { getErrorMessage } from '../../utils/format';
import type { ProfilStackParams } from '../../navigation/AppNavigator';

type Nav = NativeStackNavigationProp<ProfilStackParams>;

function fmtVol(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + ' M';
  if (n >= 1_000)     return (n / 1_000).toFixed(0) + ' k';
  return n.toFixed(0);
}

export function ProfilScreen() {
  const { logout } = useAuth();
  const navigation = useNavigation<Nav>();

  const [profil, setProfil]   = useState<ProfilData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfil = useCallback(async () => {
    setLoading(true);
    try {
      const res = await profilApi.get();
      setProfil(res.data);
    } catch (err) {
      Alert.alert('Erreur', getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { fetchProfil(); }, [fetchProfil]));

  if (loading) return <LoadingSpinner fullScreen message="Chargement du profil..." />;

  const initials = profil?.full_name
    ? profil.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : (profil?.username ?? '??').slice(0, 2).toUpperCase();

  const handleLogout = () => {
    Alert.alert('Déconnexion', 'Voulez-vous vous déconnecter ?', [
      { text: 'Annuler', style: 'cancel' },
      { text: 'Se déconnecter', style: 'destructive', onPress: logout },
    ]);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* ── HERO ─────────────────────────────────────────── */}
        <LinearGradient
          colors={[Colors.navySoft, Colors.navy, Colors.navyDeep]}
          style={styles.hero}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.heroBlob} />

          <View style={styles.heroBar}>
            <Text style={styles.heroBarTitle}>Profil</Text>
            <TouchableOpacity style={styles.editBtn} onPress={() => navigation.navigate('ModifierProfil')}>
              <Ionicons name="create-outline" size={16} color={Colors.white} />
            </TouchableOpacity>
          </View>

          <View style={styles.heroProfile}>
            <LinearGradient
              colors={[Colors.orange, Colors.orangeDeep]}
              style={styles.avatar}
            >
              <Text style={styles.avatarText}>{initials}</Text>
            </LinearGradient>
            <View style={styles.heroInfo}>
              <Text style={styles.heroName}>{profil?.full_name ?? profil?.username}</Text>
              <Text style={styles.heroUsername}>@{profil?.username} · {profil?.poste ?? 'Responsable dépôt'}</Text>
              {profil?.marketeur_nom && (
                <View style={styles.orgPill}>
                  <Ionicons name="business-outline" size={11} color={Colors.white} />
                  <Text style={styles.orgText}>{profil.marketeur_nom}</Text>
                </View>
              )}
            </View>
          </View>
        </LinearGradient>

        {/* ── STATS CARD ────────────────────────────────────── */}
        <View style={styles.statsWrap}>
          <View style={styles.statsCard}>
            {[
              { v: String(profil?.total_mouvements ?? 0),   l: 'Mouvements',         c: Colors.navy },
              { v: fmtVol(profil?.volume_total_ambiant ?? 0), l: 'Litres traités (Amb)', c: Colors.entree },
              { v: profil?.marketeur_sigle ?? profil?.marketeur_nom?.slice(0, 4).toUpperCase() ?? '—', l: 'Marketeur', c: Colors.orange },
            ].map((s, i, arr) => (
              <View key={i} style={[styles.statCol, i < arr.length - 1 && styles.statColBorder]}>
                <Text style={[styles.statValue, { color: s.c }]}>{s.v}</Text>
                <Text style={styles.statLabel}>{s.l}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* ── COORDONNÉES ──────────────────────────────────── */}
        <SectionHeader title="Coordonnées" />
        <View style={styles.pad}>
          <DetailCard rows={[
            ['Email',         profil?.email ?? null],
            ['Téléphone',     profil?.telephone ?? null],
            ['Membre depuis', profil?.date_joined
              ? new Date(profil.date_joined).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
              : null],
          ]} />
        </View>

        {/* ── PRÉFÉRENCES ──────────────────────────────────── */}
        <SectionHeader title="Préférences" />
        <View style={[styles.pad, { gap: 8 }]}>
          <PrefRow iconName="notifications-outline" label="Notifications" sub="Mouvements, alertes stock" toggle defaultOn />
          <PrefRow iconName="globe-outline"          label="Langue"        sub="Français" trail="FR" />
          <PrefRow
            iconName="shield-outline"
            label="Sécurité"
            sub="Mot de passe, biométrie"
            chev
            onPress={() => navigation.navigate('Securite')}
          />
          <BiometricRow />
        </View>

        {/* ── APPLICATION ──────────────────────────────────── */}
        <SectionHeader title="Application" />
        <View style={[styles.pad, { gap: 8 }]}>
          <PrefRow iconName="cloud-download-outline" label="Données hors ligne"    sub="Synchronisé" chev />
          <PrefRow iconName="qr-code-outline"        label="Apparier un appareil"  sub="Scanner pour ajouter" chev />
          <PrefRow
            iconName="document-text-outline"
            label="Conditions d'utilisation"
            chev
            onPress={() => navigation.navigate('ConditionsUtilisation')}
          />
        </View>

        {/* ── DÉCONNEXION ──────────────────────────────────── */}
        <View style={[styles.pad, { paddingBottom: 100, paddingTop: 18 }]}>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
            <Ionicons name="log-out-outline" size={16} color={Colors.red} />
            <Text style={styles.logoutText}>Se déconnecter</Text>
          </TouchableOpacity>
          <Text style={styles.footer}>SGDS Mobile · v2.0.0 (build 240507)</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

// ── BiometricRow ───────────────────────────────────────────────

function BiometricRow() {
  const [supported, setSupported]   = useState(false);
  const [enabled, setEnabled]       = useState(false);
  const [bioLabel, setBioLabel]     = useState('Biométrie');
  const [loading, setLoading]       = useState(false);

  useEffect(() => {
    (async () => {
      const hasHw      = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();
      if (!hasHw || !isEnrolled) return;

      setSupported(true);

      const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
      if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
        setBioLabel('Face ID');
      } else if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
        setBioLabel('Empreinte digitale');
      }

      const stored = await SecureStore.getItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED);
      setEnabled(stored === 'true');
    })();
  }, []);

  if (!supported) return null;

  const handleToggle = async (value: boolean) => {
    if (loading) return;
    setLoading(true);
    try {
      if (value) {
        const result = await LocalAuthentication.authenticateAsync({
          promptMessage:         `Activer ${bioLabel} pour SGDS`,
          cancelLabel:           'Annuler',
          disableDeviceFallback: true,
        });
        if (!result.success) { setLoading(false); return; }
        await SecureStore.setItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED, 'true');
        setEnabled(true);
        Alert.alert('Biométrie activée', `${bioLabel} sera utilisé pour vous connecter rapidement.`);
      } else {
        await SecureStore.deleteItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED);
        setEnabled(false);
      }
    } catch {
      Alert.alert('Erreur', 'Impossible de modifier le paramètre biométrique.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.prefRow}>
      <View style={styles.prefIcon}>
        <Ionicons name="finger-print" size={16} color={Colors.navy} />
      </View>
      <View style={styles.prefBody}>
        <Text style={styles.prefLabel}>{bioLabel}</Text>
        <Text style={styles.prefSub}>{enabled ? 'Activé' : 'Désactivé'}</Text>
      </View>
      <Switch
        value={enabled}
        onValueChange={handleToggle}
        trackColor={{ false: Colors.mist, true: Colors.navy }}
        thumbColor={Colors.white}
        disabled={loading}
      />
    </View>
  );
}

// ── Sous-composants ────────────────────────────────────────────

function SectionHeader({ title }: { title: string }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{title}</Text>
    </View>
  );
}

function DetailCard({ rows }: { rows: [string, string | null][] }) {
  const filtered = rows.filter(r => r[1]);
  if (filtered.length === 0) return null;
  return (
    <View style={styles.detailCard}>
      {filtered.map(([label, value], i) => (
        <View key={i} style={[styles.detailRow, i < filtered.length - 1 && styles.detailRowBorder]}>
          <Text style={styles.detailLabel}>{label}</Text>
          <Text style={styles.detailValue}>{value}</Text>
        </View>
      ))}
    </View>
  );
}

function PrefRow({
  iconName, label, sub, toggle, defaultOn, chev, trail, onPress,
}: {
  iconName: any; label: string; sub?: string;
  toggle?: boolean; defaultOn?: boolean; chev?: boolean; trail?: string;
  onPress?: () => void;
}) {
  const [on, setOn] = useState(!!defaultOn);
  return (
    <TouchableOpacity
      style={styles.prefRow}
      onPress={onPress}
      activeOpacity={onPress ? 0.7 : 1}
      disabled={!onPress && !toggle}
    >
      <View style={styles.prefIcon}>
        <Ionicons name={iconName} size={16} color={Colors.navy} />
      </View>
      <View style={styles.prefBody}>
        <Text style={styles.prefLabel}>{label}</Text>
        {sub && <Text style={styles.prefSub}>{sub}</Text>}
      </View>
      {toggle ? (
        <TouchableOpacity
          onPress={() => setOn(v => !v)}
          style={[styles.toggle, { backgroundColor: on ? Colors.navy : Colors.mist }]}
          activeOpacity={0.8}
        >
          <View style={[styles.toggleThumb, { left: on ? 18 : 2 }]} />
        </TouchableOpacity>
      ) : trail ? (
        <Text style={styles.prefTrail}>{trail}</Text>
      ) : chev ? (
        <Ionicons name="chevron-forward" size={16} color={Colors.silver} />
      ) : null}
    </TouchableOpacity>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },

  hero: {
    paddingTop: 14, paddingHorizontal: 20, paddingBottom: 80,
    overflow: 'hidden',
  },
  heroBlob: {
    position: 'absolute', top: -50, right: -50,
    width: 180, height: 180, borderRadius: 90,
    backgroundColor: Colors.orange + '1f',
  },
  heroBar: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 24,
  },
  heroBarTitle: { color: Colors.white, fontSize: 14, fontWeight: '700' },
  editBtn: {
    width: 34, height: 34, borderRadius: 10,
    backgroundColor: Colors.white + '26',
    alignItems: 'center', justifyContent: 'center',
  },
  heroProfile: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  avatar: {
    width: 74, height: 74, borderRadius: 22,
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 3, borderColor: Colors.white + '40',
    shadowColor: Colors.orange, shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.4, shadowRadius: 16,
    elevation: 6,
  },
  avatarText:   { color: Colors.white, fontSize: 30, fontWeight: '800' },
  heroInfo:     { flex: 1, minWidth: 0 },
  heroName:     { color: Colors.white, fontSize: 18, fontWeight: '800', letterSpacing: -0.3 },
  heroUsername: { color: Colors.white + 'bf', fontSize: 12, marginTop: 2 },
  orgPill: {
    marginTop: 8, flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingVertical: 4, paddingHorizontal: 10,
    backgroundColor: Colors.white + '1a',
    borderWidth: 1, borderColor: Colors.white + '22',
    borderRadius: 999, alignSelf: 'flex-start',
  },
  orgText: { color: Colors.white, fontSize: 10, fontWeight: '600' },

  statsWrap: { paddingHorizontal: 16, marginTop: -58, zIndex: 2 },
  statsCard: {
    backgroundColor: Colors.white, borderRadius: 20,
    padding: 14,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 4,
    flexDirection: 'row',
  },
  statCol:       { flex: 1, alignItems: 'center', paddingVertical: 4 },
  statColBorder: { borderRightWidth: 1, borderRightColor: Colors.cloud },
  statValue:     { fontSize: 18, fontWeight: '800' },
  statLabel:     { fontSize: 9, color: Colors.slate, fontWeight: '600', marginTop: 2, textAlign: 'center' },

  sectionHeader: { paddingHorizontal: 20, paddingTop: 22, paddingBottom: 10 },
  sectionTitle:  { fontSize: 14, fontWeight: '800', color: Colors.ink, letterSpacing: -0.2 },

  pad: { paddingHorizontal: 16 },
  detailCard: {
    backgroundColor: Colors.white, borderRadius: 20, paddingHorizontal: 16,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  detailRow:       { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12 },
  detailRowBorder: { borderBottomWidth: 1, borderBottomColor: Colors.cloud },
  detailLabel:     { fontSize: 11, color: Colors.slate, fontWeight: '600' },
  detailValue:     { fontSize: 13, color: Colors.ink, fontWeight: '600', textAlign: 'right', flex: 1 },

  prefRow: {
    backgroundColor: Colors.white, borderRadius: 14, padding: 12,
    flexDirection: 'row', alignItems: 'center', gap: 12,
    borderWidth: 1, borderColor: Colors.cloud,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 2, elevation: 1,
  },
  prefIcon: {
    width: 34, height: 34, borderRadius: 10,
    backgroundColor: Colors.navyTint,
    alignItems: 'center', justifyContent: 'center',
  },
  prefBody:  { flex: 1 },
  prefLabel: { fontSize: 13, fontWeight: '700', color: Colors.ink },
  prefSub:   { fontSize: 11, color: Colors.slate, marginTop: 1 },
  prefTrail: { fontSize: 12, color: Colors.slate, fontWeight: '600' },
  toggle: {
    width: 38, height: 22, borderRadius: 11,
    position: 'relative',
  },
  toggleThumb: {
    position: 'absolute', top: 2,
    width: 18, height: 18, borderRadius: 9,
    backgroundColor: Colors.white,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.2, shadowRadius: 2,
  },

  logoutBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    height: 50, borderRadius: 14,
    backgroundColor: Colors.redSoft,
    borderWidth: 1, borderColor: Colors.red + '30',
  },
  logoutText: { fontSize: 14, fontWeight: '700', color: Colors.red },
  footer:     { textAlign: 'center', fontSize: 10, color: Colors.silver, marginTop: 14 },
});
