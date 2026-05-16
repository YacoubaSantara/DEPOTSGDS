import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, Alert, ActivityIndicator, Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';
import dayjs from 'dayjs';

import { authApi } from '../../api/auth';
import { STORAGE_KEYS } from '../../api/client';
import { Colors, Radius } from '../../constants/colors';
import { getErrorMessage } from '../../utils/format';

export function SecurityScreen() {
  const navigation = useNavigation();

  // ── Change password state ──────────────────────────────────
  const [oldPwd,    setOldPwd]    = useState('');
  const [newPwd,    setNewPwd]    = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [showOld,   setShowOld]   = useState(false);
  const [showNew,   setShowNew]   = useState(false);
  const [showConf,  setShowConf]  = useState(false);
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdSuccess, setPwdSuccess] = useState(false);

  // ── Biometric state ────────────────────────────────────────
  const [bioSupported, setBioSupported] = useState(false);
  const [bioEnabled,   setBioEnabled]   = useState(false);
  const [bioLabel,     setBioLabel]     = useState('Biométrie');
  const [bioLoading,   setBioLoading]   = useState(false);

  // ── Session info ───────────────────────────────────────────
  const [sessionStart, setSessionStart] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const hasHw  = await LocalAuthentication.hasHardwareAsync();
      const enr    = await LocalAuthentication.isEnrolledAsync();
      if (hasHw && enr) {
        setBioSupported(true);
        const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
        if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
          setBioLabel('Face ID');
        } else if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
          setBioLabel('Empreinte digitale');
        }
        const stored = await SecureStore.getItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED);
        setBioEnabled(stored === 'true');
      }

      // Approximation de début de session via le token
      const token = await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
      if (token) {
        try {
          const part = token.split('.')[1];
          const b64  = part.replace(/-/g, '+').replace(/_/g, '/');
          const pad  = b64.padEnd(b64.length + (4 - b64.length % 4) % 4, '=');
          const payload: { iat?: number } = JSON.parse(atob(pad));
          if (payload.iat) {
            setSessionStart(dayjs(payload.iat * 1000).format('DD/MM/YYYY à HH:mm'));
          }
        } catch { /* token mal formé */ }
      }
    })();
  }, []);

  // ── Changer le mot de passe ────────────────────────────────
  const handleChangePassword = async () => {
    if (!oldPwd || !newPwd || !confirmPwd) {
      Alert.alert('Champs requis', 'Veuillez remplir tous les champs.');
      return;
    }
    if (newPwd.length < 8) {
      Alert.alert('Mot de passe trop court', 'Le nouveau mot de passe doit contenir au moins 8 caractères.');
      return;
    }
    if (newPwd !== confirmPwd) {
      Alert.alert('Erreur', 'Les deux nouveaux mots de passe ne correspondent pas.');
      return;
    }
    if (newPwd === oldPwd) {
      Alert.alert('Erreur', 'Le nouveau mot de passe doit être différent de l\'actuel.');
      return;
    }

    setPwdLoading(true);
    try {
      await authApi.changePassword(oldPwd, newPwd);

      // Mettre à jour les credentials biométriques avec le nouveau mot de passe
      const credJson = await SecureStore.getItemAsync(STORAGE_KEYS.BIOMETRIC_CREDENTIALS);
      if (credJson) {
        const creds = JSON.parse(credJson);
        await SecureStore.setItemAsync(
          STORAGE_KEYS.BIOMETRIC_CREDENTIALS,
          JSON.stringify({ ...creds, password: newPwd }),
        );
      }

      setOldPwd(''); setNewPwd(''); setConfirmPwd('');
      setPwdSuccess(true);
      setTimeout(() => setPwdSuccess(false), 3000);
    } catch (err) {
      Alert.alert('Erreur', getErrorMessage(err));
    } finally {
      setPwdLoading(false);
    }
  };

  // ── Toggle biométrie ───────────────────────────────────────
  const handleBioToggle = async (value: boolean) => {
    if (bioLoading) return;
    setBioLoading(true);
    try {
      if (value) {
        const result = await LocalAuthentication.authenticateAsync({
          promptMessage:         `Activer ${bioLabel} pour SGDS`,
          cancelLabel:           'Annuler',
          disableDeviceFallback: true,
        });
        if (!result.success) { setBioLoading(false); return; }
        await SecureStore.setItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED, 'true');
        setBioEnabled(true);
        Alert.alert('Activé', `${bioLabel} sera utilisé pour vous connecter rapidement.`);
      } else {
        await SecureStore.deleteItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED);
        setBioEnabled(false);
      }
    } catch {
      Alert.alert('Erreur', 'Impossible de modifier le paramètre biométrique.');
    } finally {
      setBioLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={20} color={Colors.ink} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Sécurité</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>

        {/* ── SESSION ACTIVE ──────────────────────────────── */}
        <View style={styles.sessionCard}>
          <View style={styles.sessionDot} />
          <View style={styles.sessionBody}>
            <Text style={styles.sessionTitle}>Session active</Text>
            <Text style={styles.sessionSub}>
              {sessionStart ? `Connecté depuis le ${sessionStart}` : 'Session en cours'}
            </Text>
          </View>
          <View style={styles.sessionBadge}>
            <Text style={styles.sessionBadgeText}>EN LIGNE</Text>
          </View>
        </View>

        {/* ── BIOMÉTRIE ───────────────────────────────────── */}
        {bioSupported && (
          <>
            <SectionHeader title="Connexion rapide" />
            <View style={styles.card}>
              <View style={styles.bioRow}>
                <View style={styles.bioIcon}>
                  <Ionicons
                    name={bioLabel === 'Face ID' ? 'scan-outline' : 'finger-print'}
                    size={20}
                    color={Colors.navy}
                  />
                </View>
                <View style={styles.bioBody}>
                  <Text style={styles.bioTitle}>{bioLabel}</Text>
                  <Text style={styles.bioSub}>
                    {bioEnabled
                      ? `Connexion par ${bioLabel} activée`
                      : `Connexion par ${bioLabel} désactivée`}
                  </Text>
                </View>
                {bioLoading
                  ? <ActivityIndicator size="small" color={Colors.navy} />
                  : (
                    <Switch
                      value={bioEnabled}
                      onValueChange={handleBioToggle}
                      trackColor={{ false: Colors.mist, true: Colors.navy }}
                      thumbColor={Colors.white}
                    />
                  )
                }
              </View>
              {bioEnabled && (
                <View style={styles.bioHint}>
                  <Ionicons name="information-circle-outline" size={14} color={Colors.slate} />
                  <Text style={styles.bioHintText}>
                    Vos identifiants sont stockés de manière chiffrée sur cet appareil.
                  </Text>
                </View>
              )}
            </View>
          </>
        )}

        {/* ── CHANGER MOT DE PASSE ────────────────────────── */}
        <SectionHeader title="Mot de passe" />
        <View style={styles.card}>
          {pwdSuccess && (
            <View style={styles.successBox}>
              <Ionicons name="checkmark-circle" size={16} color={Colors.green} />
              <Text style={styles.successText}>Mot de passe modifié avec succès</Text>
            </View>
          )}

          <PwdField
            label="Mot de passe actuel"
            value={oldPwd}
            onChangeText={setOldPwd}
            show={showOld}
            onToggleShow={() => setShowOld(v => !v)}
          />
          <View style={styles.fieldGap} />
          <PwdField
            label="Nouveau mot de passe"
            value={newPwd}
            onChangeText={setNewPwd}
            show={showNew}
            onToggleShow={() => setShowNew(v => !v)}
            hint="Minimum 8 caractères"
          />
          <View style={styles.fieldGap} />
          <PwdField
            label="Confirmer le nouveau mot de passe"
            value={confirmPwd}
            onChangeText={setConfirmPwd}
            show={showConf}
            onToggleShow={() => setShowConf(v => !v)}
          />

          <StrengthIndicator password={newPwd} />

          <TouchableOpacity
            style={[styles.pwdBtn, pwdLoading && styles.pwdBtnDisabled]}
            onPress={handleChangePassword}
            disabled={pwdLoading}
            activeOpacity={0.8}
          >
            {pwdLoading
              ? <ActivityIndicator color={Colors.white} />
              : (
                <>
                  <Ionicons name="key-outline" size={16} color={Colors.white} />
                  <Text style={styles.pwdBtnText}>Modifier le mot de passe</Text>
                </>
              )
            }
          </TouchableOpacity>
        </View>

        {/* ── CONSEILS ────────────────────────────────────── */}
        <SectionHeader title="Bonnes pratiques" />
        <View style={styles.card}>
          {[
            { icon: 'lock-closed-outline',   text: 'Utilisez un mot de passe unique, non partagé avec d\'autres services.' },
            { icon: 'refresh-outline',        text: 'Changez votre mot de passe tous les 3 mois.' },
            { icon: 'phone-portrait-outline', text: 'Ne partagez jamais vos identifiants avec un collègue.' },
            { icon: 'wifi-outline',           text: 'Évitez de vous connecter sur un réseau Wi-Fi public.' },
          ].map((tip, i, arr) => (
            <View
              key={i}
              style={[styles.tipRow, i < arr.length - 1 && styles.tipRowBorder]}
            >
              <View style={styles.tipIcon}>
                <Ionicons name={tip.icon as any} size={15} color={Colors.navy} />
              </View>
              <Text style={styles.tipText}>{tip.text}</Text>
            </View>
          ))}
        </View>

        <View style={{ height: 60 }} />
      </ScrollView>
    </SafeAreaView>
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

function PwdField({
  label, value, onChangeText, show, onToggleShow, hint,
}: {
  label: string; value: string; onChangeText: (v: string) => void;
  show: boolean; onToggleShow: () => void; hint?: string;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <View>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={[styles.fieldRow, focused && styles.fieldFocused]}>
        <Ionicons name="lock-closed-outline" size={16} color={focused ? Colors.navy : Colors.slate} />
        <TextInput
          style={styles.fieldInput}
          value={value}
          onChangeText={onChangeText}
          secureTextEntry={!show}
          autoCapitalize="none"
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholderTextColor={Colors.silver}
          placeholder="••••••••"
        />
        <TouchableOpacity onPress={onToggleShow} style={{ padding: 4 }}>
          <Ionicons
            name={show ? 'eye-off-outline' : 'eye-outline'}
            size={16}
            color={Colors.slate}
          />
        </TouchableOpacity>
      </View>
      {hint && <Text style={styles.fieldHint}>{hint}</Text>}
    </View>
  );
}

function StrengthIndicator({ password }: { password: string }) {
  if (!password) return null;

  let score = 0;
  if (password.length >= 8)  score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const levels = [
    { label: 'Très faible', color: Colors.red },
    { label: 'Faible',      color: Colors.red },
    { label: 'Moyen',       color: Colors.amber },
    { label: 'Fort',        color: Colors.green },
    { label: 'Très fort',   color: Colors.green },
  ];
  const { label, color } = levels[Math.min(score, 4)];

  return (
    <View style={styles.strengthWrap}>
      <View style={styles.strengthBars}>
        {[0, 1, 2, 3, 4].map(i => (
          <View
            key={i}
            style={[
              styles.strengthBar,
              { backgroundColor: i <= score ? color : Colors.cloud },
            ]}
          />
        ))}
      </View>
      <Text style={[styles.strengthLabel, { color }]}>{label}</Text>
    </View>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: Colors.paper },
  content: { padding: 16 },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    backgroundColor: Colors.white,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: Colors.cloud,
    alignItems: 'center', justifyContent: 'center',
  },
  headerTitle: { fontSize: 15, fontWeight: '800', color: Colors.ink, letterSpacing: -0.2 },

  sessionCard: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: Colors.greenSoft,
    borderRadius: Radius.lg, padding: 14, marginBottom: 4,
    borderWidth: 1, borderColor: Colors.green + '30',
  },
  sessionDot: {
    width: 10, height: 10, borderRadius: 5,
    backgroundColor: Colors.green,
    shadowColor: Colors.green, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.5, shadowRadius: 4,
  },
  sessionBody:  { flex: 1 },
  sessionTitle: { fontSize: 13, fontWeight: '700', color: Colors.ink },
  sessionSub:   { fontSize: 11, color: Colors.slate, marginTop: 1 },
  sessionBadge: {
    backgroundColor: Colors.green,
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6,
  },
  sessionBadgeText: { fontSize: 9, fontWeight: '800', color: Colors.white, letterSpacing: 0.5 },

  sectionHeader: { paddingTop: 22, paddingBottom: 10, paddingHorizontal: 2 },
  sectionTitle:  { fontSize: 14, fontWeight: '800', color: Colors.ink, letterSpacing: -0.2 },

  card: {
    backgroundColor: Colors.white, borderRadius: Radius.lg, padding: 16,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
    borderWidth: 1, borderColor: Colors.cloud,
  },

  // Biométrie
  bioRow:  { flexDirection: 'row', alignItems: 'center', gap: 12 },
  bioIcon: {
    width: 42, height: 42, borderRadius: 13,
    backgroundColor: Colors.navyTint,
    alignItems: 'center', justifyContent: 'center',
  },
  bioBody:  { flex: 1 },
  bioTitle: { fontSize: 14, fontWeight: '700', color: Colors.ink },
  bioSub:   { fontSize: 11, color: Colors.slate, marginTop: 1 },
  bioHint: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 6,
    marginTop: 12, paddingTop: 12,
    borderTopWidth: 1, borderTopColor: Colors.cloud,
  },
  bioHintText: { flex: 1, fontSize: 11, color: Colors.slate, lineHeight: 16 },

  // Succès
  successBox: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: Colors.greenSoft,
    borderRadius: 10, padding: 10, marginBottom: 16,
    borderWidth: 1, borderColor: Colors.green + '40',
  },
  successText: { fontSize: 13, fontWeight: '600', color: Colors.green },

  // Champs mot de passe
  fieldLabel: { fontSize: 11, color: Colors.slate, fontWeight: '600', marginBottom: 6, letterSpacing: 0.2 },
  fieldRow: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    height: 48, paddingHorizontal: 12,
    backgroundColor: Colors.cloud,
    borderRadius: Radius.md,
    borderWidth: 1.5, borderColor: 'transparent',
  },
  fieldFocused: { backgroundColor: Colors.white, borderColor: Colors.navy },
  fieldInput:   { flex: 1, fontSize: 14, color: Colors.ink, paddingVertical: 0 },
  fieldHint:    { fontSize: 10, color: Colors.slate, marginTop: 4 },
  fieldGap:     { height: 12 },

  // Indicateur de force
  strengthWrap: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 10, marginBottom: 16 },
  strengthBars: { flexDirection: 'row', gap: 4, flex: 1 },
  strengthBar:  { flex: 1, height: 4, borderRadius: 2 },
  strengthLabel:{ fontSize: 11, fontWeight: '700', minWidth: 60, textAlign: 'right' },

  // Bouton modifier
  pwdBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    height: 48, borderRadius: Radius.md,
    backgroundColor: Colors.navy,
  },
  pwdBtnDisabled: { backgroundColor: Colors.slate },
  pwdBtnText: { color: Colors.white, fontSize: 14, fontWeight: '700' },

  // Conseils
  tipRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, paddingVertical: 12 },
  tipRowBorder: { borderBottomWidth: 1, borderBottomColor: Colors.cloud },
  tipIcon: {
    width: 30, height: 30, borderRadius: 9,
    backgroundColor: Colors.navyTint,
    alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },
  tipText: { flex: 1, fontSize: 12, color: Colors.graphite, lineHeight: 18 },
});
