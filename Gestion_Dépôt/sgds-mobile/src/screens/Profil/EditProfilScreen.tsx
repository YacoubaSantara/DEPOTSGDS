import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, Alert, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';

import { profilApi } from '../../api/profil';
import { Colors, Radius } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { getErrorMessage } from '../../utils/format';

export function EditProfilScreen() {
  const navigation = useNavigation();

  const [loading, setLoading]       = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName]   = useState('');
  const [email, setEmail]         = useState('');
  const [telephone, setTelephone] = useState('');

  useFocusEffect(useCallback(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await profilApi.get();
        setFirstName(res.data.first_name ?? '');
        setLastName(res.data.last_name ?? '');
        setEmail(res.data.email ?? '');
        setTelephone(res.data.telephone ?? '');
      } catch (err) {
        Alert.alert('Erreur', getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []));

  const handleSubmit = async () => {
    if (!firstName.trim() || !lastName.trim()) {
      Alert.alert('Champs requis', 'Le prénom et le nom sont obligatoires.');
      return;
    }
    setSubmitting(true);
    try {
      await profilApi.update({
        first_name: firstName.trim(),
        last_name:  lastName.trim(),
        email:      email.trim(),
        telephone:  telephone.trim(),
      });
      navigation.goBack();
    } catch (err) {
      Alert.alert('Erreur', getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner fullScreen message="Chargement du profil..." />;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={20} color={Colors.ink} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Modifier le profil</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Field label="Prénom *" value={firstName} onChangeText={setFirstName} placeholder="Prénom" />
        <Field label="Nom *" value={lastName} onChangeText={setLastName} placeholder="Nom de famille" />
        <Field label="Email" value={email} onChangeText={setEmail} placeholder="vous@email.com" keyboardType="email-address" />
        <Field label="Téléphone" value={telephone} onChangeText={setTelephone} placeholder="+223 70 xx xx xx" keyboardType="phone-pad" />

        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          {submitting
            ? <ActivityIndicator color={Colors.white} />
            : <Text style={styles.submitBtnText}>Enregistrer</Text>}
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function Field({
  label, value, onChangeText, placeholder, keyboardType,
}: {
  label: string; value: string; onChangeText: (v: string) => void;
  placeholder?: string; keyboardType?: 'phone-pad' | 'email-address';
}) {
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={Colors.silver}
        keyboardType={keyboardType}
        autoCapitalize={keyboardType === 'email-address' ? 'none' : 'sentences'}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },
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
  headerTitle: { fontSize: 15, fontWeight: '800', color: Colors.ink },

  content: { padding: 16 },

  fieldWrap: { marginBottom: 16 },
  fieldLabel: { fontSize: 11, color: Colors.slate, fontWeight: '700', marginBottom: 6, letterSpacing: 0.2 },
  input: {
    height: 48, paddingHorizontal: 14,
    backgroundColor: Colors.white, borderRadius: Radius.md,
    borderWidth: 1, borderColor: Colors.cloud,
    fontSize: 14, color: Colors.ink,
  },

  submitBtn: {
    height: 50, borderRadius: Radius.md, backgroundColor: Colors.navy,
    alignItems: 'center', justifyContent: 'center', marginTop: 12,
  },
  submitBtnDisabled: { backgroundColor: Colors.slate },
  submitBtnText: { color: Colors.white, fontSize: 14, fontWeight: '700' },
});
