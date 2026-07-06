import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert,
  InteractionManager,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as SecureStore from '../../utils/secureStorage';
import * as LocalAuthentication from 'expo-local-authentication';
import { useAuth } from '../../context/AuthContext';
import { STORAGE_KEYS } from '../../api/client';
import { Colors, Radius, Spacing, FontSize } from '../../constants/colors';
import { getErrorMessage } from '../../utils/format';

export function LoginScreen() {
  const { login, loginWithBiometric } = useAuth();
  const [username, setUsername]         = useState('');
  const [password, setPassword]         = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading]           = useState(false);
  const [bioLoading, setBioLoading]     = useState(false);
  const [error, setError]               = useState<string | null>(null);
  const [bioEnabled, setBioEnabled]     = useState(false);
  const [bioLabel, setBioLabel]         = useState('Biométrie');
  const [bioIcon, setBioIcon]           = useState<'finger-print' | 'scan-outline'>('finger-print');

  // Vérifie si la biométrie est activée et disponible
  useEffect(() => {
    (async () => {
      const stored   = await SecureStore.getItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED);
      const hasHw    = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();
      const hasCreds = await SecureStore.getItemAsync(STORAGE_KEYS.BIOMETRIC_CREDENTIALS);

      if (stored === 'true' && hasHw && enrolled && hasCreds) {
        const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
        if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
          setBioLabel('Face ID');
          setBioIcon('scan-outline');
        } else {
          setBioLabel('Empreinte digitale');
          setBioIcon('finger-print');
        }
        setBioEnabled(true);
        // Auto-prompt biométrique au chargement, une fois les animations/transitions terminées
        // (sinon l'OS annule le prompt trop tôt avec system_cancel pendant le montage de l'écran)
        InteractionManager.runAfterInteractions(() => {
          handleBiometricLogin(true);
        });
      }
    })();
  }, []);

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      setError('Veuillez remplir tous les champs.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await login({ username: username.trim(), password });
      // Propose d'activer la biométrie si non activée et si supportée
      const hasHw    = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();
      const stored   = await SecureStore.getItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED);
      if (hasHw && enrolled && stored !== 'true') {
        Alert.alert(
          'Connexion biométrique',
          'Voulez-vous activer la connexion rapide par biométrie (empreinte/Face ID) pour les prochaines connexions ?',
          [
            { text: 'Plus tard', style: 'cancel' },
            {
              text: 'Activer',
              onPress: async () => {
                await SecureStore.setItemAsync(STORAGE_KEYS.BIOMETRIC_ENABLED, 'true');
              },
            },
          ],
        );
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleBiometricLogin = async (auto = false) => {
    if (bioLoading) return;
    setBioLoading(true);
    setError(null);
    try {
      await loginWithBiometric();
    } catch (err) {
      // La tentative automatique au lancement peut être annulée par le système
      // (transition d'écran, app pas encore au premier plan) : on ne l'affiche
      // pas comme une erreur, l'utilisateur peut toujours appuyer sur le bouton.
      if (!auto) {
        setError(getErrorMessage(err));
      }
    } finally {
      setBioLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'android' ? 20 : 0}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          bounces={false}
        >
          {/* ── HERO ─────────────────────────────────────────── */}
          <LinearGradient
            colors={[Colors.navySoft, Colors.navy, Colors.navyDeep]}
            style={styles.hero}
            start={{ x: 0.2, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <View style={styles.blob1} />
            <View style={styles.blob2} />

            <View style={styles.logoRow}>
              <LinearGradient
                colors={[Colors.orange, Colors.orangeDeep]}
                style={styles.logoBadge}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="water" size={20} color={Colors.white} />
              </LinearGradient>
              <View>
                <Text style={styles.logoName}>SGDS</Text>
                <Text style={styles.logoSub}>Mobile · v2.0</Text>
              </View>
            </View>

            <View style={styles.taglineBlock}>
              <Text style={styles.taglineGreet}>Bienvenue</Text>
              <Text style={styles.taglineTitle}>
                {'Vos dépôts.\n'}
                <Text style={{ color: Colors.orange }}>En temps réel.</Text>
              </Text>
              <Text style={styles.taglineSub}>
                Système de Gestion des Dépôts pétroliers — édition mobile.
              </Text>
            </View>
          </LinearGradient>

          {/* ── FORM CARD ────────────────────────────────────── */}
          <View style={styles.card}>
            <View style={styles.handle} />
            <Text style={styles.cardTitle}>Connexion</Text>
            <Text style={styles.cardSub}>Compte marketeur</Text>

            {error && (
              <View style={styles.errorBox}>
                <Ionicons name="alert-circle" size={15} color={Colors.red} />
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}

            <View style={{ marginTop: 22 }}>
              <Field
                label="Identifiant"
                iconName="person-outline"
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
                returnKeyType="next"
              />
              <View style={{ height: 14 }} />
              <Field
                label="Mot de passe"
                iconName="lock-closed-outline"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                returnKeyType="done"
                onSubmitEditing={handleLogin}
                trailing={
                  <TouchableOpacity
                    onPress={() => setShowPassword(v => !v)}
                    style={styles.eyeBtn}
                  >
                    <Ionicons
                      name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                      size={18}
                      color={Colors.slate}
                    />
                  </TouchableOpacity>
                }
              />
            </View>

            <TouchableOpacity style={styles.forgotRow}>
              <Text style={styles.forgotText}>Mot de passe oublié ?</Text>
            </TouchableOpacity>

            {/* Bouton connexion */}
            <TouchableOpacity
              onPress={handleLogin}
              disabled={loading}
              activeOpacity={0.85}
              style={styles.loginBtnWrap}
            >
              <LinearGradient
                colors={loading ? [Colors.slate, Colors.slate] : [Colors.navy, Colors.navyDeep]}
                style={styles.loginBtn}
                start={{ x: 0, y: 0 }}
                end={{ x: 0, y: 1 }}
              >
                {loading ? (
                  <ActivityIndicator color={Colors.white} />
                ) : (
                  <>
                    <Text style={styles.loginBtnText}>Se connecter</Text>
                    <Ionicons name="arrow-forward" size={16} color={Colors.white} />
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>

            {/* Biométrie — visible uniquement si activée */}
            {bioEnabled && (
              <TouchableOpacity
                style={styles.bioRow}
                onPress={() => handleBiometricLogin()}
                disabled={bioLoading}
                activeOpacity={0.8}
              >
                <View style={styles.bioIcon}>
                  {bioLoading
                    ? <ActivityIndicator size="small" color={Colors.navy} />
                    : <Ionicons name={bioIcon} size={20} color={Colors.navy} />
                  }
                </View>
                <View style={styles.bioTexts}>
                  <Text style={styles.bioTitle}>Se connecter avec {bioLabel}</Text>
                  <Text style={styles.bioSub}>Touchez pour vous authentifier</Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color={Colors.silver} />
              </TouchableOpacity>
            )}

            <Text style={styles.footer}>© SANKE · SGDS Mobile · v2.0.0</Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ── Composant champ ────────────────────────────────────────────
interface FieldProps {
  label: string;
  iconName: any;
  value: string;
  onChangeText: (v: string) => void;
  secureTextEntry?: boolean;
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  returnKeyType?: 'next' | 'done';
  onSubmitEditing?: () => void;
  trailing?: React.ReactNode;
}

function Field({ label, iconName, value, onChangeText, trailing, ...rest }: FieldProps) {
  const [focused, setFocused] = useState(false);
  return (
    <View>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={[styles.fieldRow, focused && styles.fieldRowFocused]}>
        <Ionicons name={iconName} size={18} color={focused ? Colors.navy : Colors.slate} />
        <TextInput
          style={styles.fieldInput}
          value={value}
          onChangeText={onChangeText}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholderTextColor={Colors.silver}
          {...rest}
        />
        {trailing}
      </View>
    </View>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe:          { flex: 1, backgroundColor: Colors.navyDeep },
  flex:          { flex: 1 },
  scrollContent: { flexGrow: 1 },

  hero: {
    paddingTop: 28, paddingHorizontal: 28, paddingBottom: 48,
    overflow: 'hidden',
  },
  blob1: {
    position: 'absolute', top: -80, right: -60,
    width: 240, height: 240, borderRadius: 120,
    backgroundColor: Colors.orange + '22',
  },
  blob2: {
    position: 'absolute', bottom: -100, left: -40,
    width: 200, height: 200, borderRadius: 100,
    backgroundColor: Colors.navySoft + '55',
  },
  logoRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 32 },
  logoBadge: {
    width: 38, height: 38, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: Colors.orange, shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.45, shadowRadius: 10, elevation: 8,
  },
  logoName: { color: Colors.white, fontWeight: '800', fontSize: 15, letterSpacing: 0.4 },
  logoSub:  { color: Colors.white + 'b3', fontSize: 10, letterSpacing: 1, textTransform: 'uppercase' },
  taglineBlock: {},
  taglineGreet: { color: Colors.white + 'bf', fontSize: 13, fontWeight: '500', marginBottom: 6 },
  taglineTitle: { color: Colors.white, fontSize: 26, fontWeight: '800', lineHeight: 30, letterSpacing: -0.5 },
  taglineSub:   { color: Colors.white + 'a6', fontSize: 12, marginTop: 8, lineHeight: 18, maxWidth: 280 },

  card: {
    flex: 1, marginTop: -24,
    backgroundColor: Colors.white,
    borderTopLeftRadius: 28, borderTopRightRadius: 28,
    paddingHorizontal: 24, paddingBottom: 40,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: -8 }, shadowOpacity: 0.04, shadowRadius: 16, elevation: 4,
  },
  handle: {
    width: 40, height: 4, borderRadius: 2,
    backgroundColor: Colors.mist,
    alignSelf: 'center', marginTop: 10, marginBottom: 22,
  },
  cardTitle: { fontSize: 18, fontWeight: '800', color: Colors.ink },
  cardSub:   { fontSize: 12, color: Colors.slate, marginTop: 4 },

  errorBox: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: Colors.redSoft,
    borderRadius: Radius.sm, padding: Spacing.sm, marginTop: 14,
  },
  errorText: { flex: 1, fontSize: FontSize.sm, color: Colors.red },

  fieldLabel: {
    fontSize: 11, color: Colors.slate, fontWeight: '600',
    marginBottom: 6, letterSpacing: 0.2,
  },
  fieldRow: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    height: 50, paddingHorizontal: 12,
    backgroundColor: Colors.cloud,
    borderRadius: Radius.md,
    borderWidth: 1.5, borderColor: 'transparent',
  },
  fieldRowFocused: { backgroundColor: Colors.white, borderColor: Colors.navy },
  fieldInput: { flex: 1, fontSize: 15, fontWeight: '500', color: Colors.ink, paddingVertical: 0 },
  eyeBtn: { padding: 6 },

  forgotRow: { alignItems: 'flex-end', marginTop: 10 },
  forgotText: { color: Colors.navy, fontSize: 12, fontWeight: '600' },

  loginBtnWrap: { marginTop: 20, borderRadius: Radius.md, overflow: 'hidden' },
  loginBtn: {
    height: 52, flexDirection: 'row',
    alignItems: 'center', justifyContent: 'center', gap: 8,
    shadowColor: Colors.navy,
    shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.30, shadowRadius: 12, elevation: 6,
  },
  loginBtnText: { color: Colors.white, fontWeight: '700', fontSize: 15, letterSpacing: 0.2 },

  bioRow: {
    marginTop: 14, padding: 12,
    backgroundColor: Colors.cloud, borderRadius: 12,
    flexDirection: 'row', alignItems: 'center', gap: 10,
    borderWidth: 1, borderColor: Colors.navy + '20',
  },
  bioIcon: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: Colors.white,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: Colors.navy, shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2,
  },
  bioTexts: { flex: 1 },
  bioTitle: { fontSize: 13, fontWeight: '700', color: Colors.ink },
  bioSub:   { fontSize: 10, color: Colors.slate, marginTop: 1 },

  footer: { textAlign: 'center', fontSize: 10, color: Colors.silver, marginTop: 18 },
});
