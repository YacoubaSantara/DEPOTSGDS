import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, Alert, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { camionsApi, Compartiment } from '../../api/camions';
import { Colors, Radius } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { getErrorMessage } from '../../utils/format';
import type { FlotteStackParams } from '../../navigation/AppNavigator';

type Nav = NativeStackNavigationProp<FlotteStackParams>;
type Rt  = RouteProp<FlotteStackParams, 'CamionForm'>;

const TYPE_PRODUIT_CHOICES = [
  { key: 'Carburant', label: 'Carburant' },
  { key: 'HUILE',     label: 'Huile' },
  { key: 'MIXTE',     label: 'Mixte' },
  { key: 'AUTRE',     label: 'Autre' },
];

const STATUT_CHOICES = [
  { key: 'EN_SERVICE',     label: 'En service' },
  { key: 'HORS_SERVICE',   label: 'Hors service' },
  { key: 'EN_MAINTENANCE', label: 'Maintenance' },
  { key: 'RETIRE',         label: 'Retiré' },
];

export function CamionFormScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<Rt>();
  const editId = route.params?.id;
  const isEdit = !!editId;

  const [loading, setLoading]       = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);

  const [immatriculation, setImmatriculation] = useState('');
  const [marque, setMarque]                   = useState('');
  const [modele, setModele]                   = useState('');
  const [capaciteTotale, setCapaciteTotale]   = useState('');
  const [typeProduit, setTypeProduit]         = useState('Carburant');
  const [statut, setStatut]                   = useState('EN_SERVICE');
  const [notes, setNotes]                     = useState('');
  const [compartiments, setCompartiments]     = useState<Compartiment[]>([{ numero: 1, capacite: 0 }]);

  useFocusEffect(useCallback(() => {
    if (!editId) return;
    (async () => {
      setLoading(true);
      try {
        const res = await camionsApi.detail(editId);
        const c = res.data;
        setImmatriculation(c.immatriculation);
        setMarque(c.marque);
        setModele(c.modele ?? '');
        setCapaciteTotale(String(c.capacite_totale));
        setTypeProduit(c.type_produit);
        setStatut(c.statut);
        setNotes(c.notes ?? '');
        setCompartiments(c.compartiments.length ? c.compartiments : [{ numero: 1, capacite: 0 }]);
      } catch (err) {
        Alert.alert('Erreur', getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, [editId]));

  const addCompartiment = () => {
    setCompartiments(prev => [...prev, { numero: prev.length + 1, capacite: 0 }]);
  };

  const removeCompartiment = (index: number) => {
    setCompartiments(prev =>
      prev.filter((_, i) => i !== index).map((c, i) => ({ ...c, numero: i + 1 })),
    );
  };

  const updateCompartimentCapacite = (index: number, value: string) => {
    const n = parseFloat(value.replace(',', '.')) || 0;
    setCompartiments(prev => prev.map((c, i) => (i === index ? { ...c, capacite: n } : c)));
  };

  const handleSubmit = async () => {
    if (!immatriculation.trim() || !marque.trim() || !capaciteTotale.trim()) {
      Alert.alert('Champs requis', 'Immatriculation, marque et capacité totale sont obligatoires.');
      return;
    }
    const payload = {
      immatriculation: immatriculation.trim(),
      marque: marque.trim(),
      modele: modele.trim() || undefined,
      capacite_totale: parseFloat(capaciteTotale.replace(',', '.')) || 0,
      nombre_compartiments: compartiments.length,
      type_produit: typeProduit,
      statut,
      notes: notes.trim() || undefined,
      compartiments,
    };

    setSubmitting(true);
    try {
      if (isEdit && editId) {
        await camionsApi.update(editId, payload);
      } else {
        await camionsApi.create(payload);
      }
      navigation.goBack();
    } catch (err) {
      Alert.alert('Erreur', getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner fullScreen message="Chargement..." />;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={20} color={Colors.ink} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{isEdit ? 'Modifier le camion' : 'Nouveau camion'}</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Field label="Immatriculation *" value={immatriculation} onChangeText={setImmatriculation} placeholder="Ex: 00 ML 1234 A" />
        <Field label="Marque *" value={marque} onChangeText={setMarque} placeholder="Ex: Mercedes-Benz" />
        <Field label="Modèle" value={modele} onChangeText={setModele} placeholder="Ex: Actros 2545" />
        <Field label="Capacité totale (litres) *" value={capaciteTotale} onChangeText={setCapaciteTotale} placeholder="Ex: 35000" keyboardType="numeric" />

        <Text style={styles.fieldLabel}>Type de produit</Text>
        <ChipRow choices={TYPE_PRODUIT_CHOICES} value={typeProduit} onChange={setTypeProduit} />

        <Text style={styles.fieldLabel}>Statut</Text>
        <ChipRow choices={STATUT_CHOICES} value={statut} onChange={setStatut} />

        <View style={styles.compHeader}>
          <Text style={styles.fieldLabel}>Compartiments ({compartiments.length})</Text>
          <TouchableOpacity onPress={addCompartiment} style={styles.addCompBtn}>
            <Ionicons name="add" size={16} color={Colors.navy} />
          </TouchableOpacity>
        </View>
        {compartiments.map((c, i) => (
          <View key={i} style={styles.compRow}>
            <Text style={styles.compNum}>C{c.numero}</Text>
            <TextInput
              style={styles.compInput}
              value={c.capacite ? String(c.capacite) : ''}
              onChangeText={(v) => updateCompartimentCapacite(i, v)}
              placeholder="Capacité (L)"
              placeholderTextColor={Colors.silver}
              keyboardType="numeric"
            />
            {compartiments.length > 1 && (
              <TouchableOpacity onPress={() => removeCompartiment(i)} style={{ padding: 6 }}>
                <Ionicons name="close-circle" size={18} color={Colors.red} />
              </TouchableOpacity>
            )}
          </View>
        ))}

        <Field label="Notes" value={notes} onChangeText={setNotes} placeholder="Observations…" multiline />

        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          {submitting
            ? <ActivityIndicator color={Colors.white} />
            : <Text style={styles.submitBtnText}>{isEdit ? 'Enregistrer' : 'Créer le camion'}</Text>}
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function Field({
  label, value, onChangeText, placeholder, keyboardType, multiline,
}: {
  label: string; value: string; onChangeText: (v: string) => void;
  placeholder?: string; keyboardType?: 'numeric'; multiline?: boolean;
}) {
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        style={[styles.input, multiline && styles.inputMultiline]}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={Colors.silver}
        keyboardType={keyboardType}
        multiline={multiline}
        numberOfLines={multiline ? 3 : 1}
      />
    </View>
  );
}

function ChipRow({ choices, value, onChange }: {
  choices: { key: string; label: string }[]; value: string; onChange: (v: string) => void;
}) {
  return (
    <View style={styles.chipRow}>
      {choices.map(c => {
        const active = value === c.key;
        return (
          <TouchableOpacity
            key={c.key}
            onPress={() => onChange(c.key)}
            style={[styles.chip, { backgroundColor: active ? Colors.navy : Colors.cloud }]}
          >
            <Text style={[styles.chipText, { color: active ? Colors.white : Colors.graphite }]}>{c.label}</Text>
          </TouchableOpacity>
        );
      })}
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
  inputMultiline: { height: 80, paddingTop: 12, textAlignVertical: 'top' },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderRadius: 999 },
  chipText: { fontSize: 12, fontWeight: '700' },

  compHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  addCompBtn: {
    width: 30, height: 30, borderRadius: 9,
    backgroundColor: Colors.navyTint,
    alignItems: 'center', justifyContent: 'center',
  },
  compRow: {
    flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8,
  },
  compNum: { width: 32, fontSize: 12, fontWeight: '700', color: Colors.graphite },
  compInput: {
    flex: 1, height: 44, paddingHorizontal: 12,
    backgroundColor: Colors.white, borderRadius: Radius.md,
    borderWidth: 1, borderColor: Colors.cloud,
    fontSize: 13, color: Colors.ink,
  },

  submitBtn: {
    height: 50, borderRadius: Radius.md, backgroundColor: Colors.navy,
    alignItems: 'center', justifyContent: 'center', marginTop: 12,
  },
  submitBtnDisabled: { backgroundColor: Colors.slate },
  submitBtnText: { color: Colors.white, fontSize: 14, fontWeight: '700' },
});
