import React, { useState, useCallback, useMemo } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, Alert, ActivityIndicator, Modal, FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { chauffeursApi } from '../../api/chauffeurs';
import { camionsApi, Camion } from '../../api/camions';
import { Colors, Radius } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { getErrorMessage } from '../../utils/format';
import type { FlotteStackParams } from '../../navigation/AppNavigator';

type Nav = NativeStackNavigationProp<FlotteStackParams>;
type Rt  = RouteProp<FlotteStackParams, 'ChauffeurForm'>;

const CATEGORIE_CHOICES = ['B', 'C', 'D', 'CE', 'C1E', 'AUTRE'];
const STATUT_CHOICES = [
  { key: 'ACTIF', label: 'Actif' },
  { key: 'INACTIF', label: 'Inactif' },
  { key: 'SUSPENDU', label: 'Suspendu' },
];

export function ChauffeurFormScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<Rt>();
  const editId = route.params?.id;
  const isEdit = !!editId;

  const [loading, setLoading]       = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [camions, setCamions]       = useState<Camion[]>([]);

  const [nom, setNom]                     = useState('');
  const [prenom, setPrenom]               = useState('');
  const [telephone, setTelephone]         = useState('');
  const [telephone2, setTelephone2]       = useState('');
  const [email, setEmail]                 = useState('');
  const [numeroPermis, setNumeroPermis]   = useState('');
  const [categoriePermis, setCategoriePermis] = useState('B');
  const [statut, setStatut]               = useState('ACTIF');
  const [camionId, setCamionId]           = useState<number | null>(null);
  const [dateEmbauche, setDateEmbauche]   = useState('');
  const [notes, setNotes]                 = useState('');

  const [camionModalVisible, setCamionModalVisible] = useState(false);
  const [camionSearch, setCamionSearch]             = useState('');

  const selectedCamion = useMemo(
    () => camions.find(c => c.id === camionId) ?? null,
    [camions, camionId],
  );

  const filteredCamions = useMemo(() => {
    if (!camionSearch.trim()) return camions;
    const q = camionSearch.toLowerCase();
    return camions.filter(c =>
      c.immatriculation.toLowerCase().includes(q) || c.marque.toLowerCase().includes(q)
    );
  }, [camions, camionSearch]);

  const openCamionModal = () => {
    setCamionSearch('');
    setCamionModalVisible(true);
  };

  const selectCamion = (id: number | null) => {
    setCamionId(id);
    setCamionModalVisible(false);
  };

  useFocusEffect(useCallback(() => {
    (async () => {
      setLoading(true);
      try {
        const camionsRes = await camionsApi.list({ statut: 'EN_SERVICE' });
        setCamions(camionsRes.data);

        if (editId) {
          const res = await chauffeursApi.detail(editId);
          const c = res.data;
          setNom(c.nom);
          setPrenom(c.prenom);
          setTelephone(c.telephone);
          setTelephone2(c.telephone2 ?? '');
          setEmail(c.email ?? '');
          setNumeroPermis(c.numero_permis);
          setCategoriePermis(c.categorie_permis);
          setStatut(c.statut);
          setCamionId(c.camion);
          setDateEmbauche(c.date_embauche ?? '');
          setNotes(c.notes ?? '');
        }
      } catch (err) {
        Alert.alert('Erreur', getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, [editId]));

  const handleSubmit = async () => {
    if (!nom.trim() || !prenom.trim() || !telephone.trim() || !numeroPermis.trim()) {
      Alert.alert('Champs requis', 'Nom, prénom, téléphone et n° permis sont obligatoires.');
      return;
    }
    const payload = {
      nom: nom.trim(),
      prenom: prenom.trim(),
      telephone: telephone.trim(),
      telephone2: telephone2.trim() || undefined,
      email: email.trim() || undefined,
      numero_permis: numeroPermis.trim(),
      categorie_permis: categoriePermis,
      statut,
      camion: camionId,
      date_embauche: dateEmbauche.trim() || undefined,
      notes: notes.trim() || undefined,
    };

    setSubmitting(true);
    try {
      if (isEdit && editId) {
        await chauffeursApi.update(editId, payload);
      } else {
        await chauffeursApi.create(payload);
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
        <Text style={styles.headerTitle}>{isEdit ? 'Modifier le chauffeur' : 'Nouveau chauffeur'}</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Field label="Nom *" value={nom} onChangeText={setNom} placeholder="Nom de famille" />
        <Field label="Prénom *" value={prenom} onChangeText={setPrenom} placeholder="Prénom(s)" />
        <Field label="Téléphone *" value={telephone} onChangeText={setTelephone} placeholder="+223 70 xx xx xx" keyboardType="phone-pad" />
        <Field label="Téléphone 2" value={telephone2} onChangeText={setTelephone2} placeholder="+223 65 xx xx xx" keyboardType="phone-pad" />
        <Field label="Email" value={email} onChangeText={setEmail} placeholder="chauffeur@email.com" keyboardType="email-address" />
        <Field label="N° Permis de conduire *" value={numeroPermis} onChangeText={setNumeroPermis} placeholder="N° permis" />

        <Text style={styles.fieldLabel}>Catégorie permis</Text>
        <View style={styles.chipRow}>
          {CATEGORIE_CHOICES.map(cat => {
            const active = categoriePermis === cat;
            return (
              <TouchableOpacity
                key={cat}
                onPress={() => setCategoriePermis(cat)}
                style={[styles.chip, { backgroundColor: active ? Colors.navy : Colors.cloud }]}
              >
                <Text style={[styles.chipText, { color: active ? Colors.white : Colors.graphite }]}>{cat}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <Text style={styles.fieldLabel}>Statut</Text>
        <View style={styles.chipRow}>
          {STATUT_CHOICES.map(s => {
            const active = statut === s.key;
            return (
              <TouchableOpacity
                key={s.key}
                onPress={() => setStatut(s.key)}
                style={[styles.chip, { backgroundColor: active ? Colors.navy : Colors.cloud }]}
              >
                <Text style={[styles.chipText, { color: active ? Colors.white : Colors.graphite }]}>{s.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.fieldWrap}>
          <Text style={styles.fieldLabel}>Camion assigné</Text>
          <TouchableOpacity style={styles.selectField} onPress={openCamionModal} activeOpacity={0.7}>
            <Ionicons name="car-outline" size={16} color={Colors.slate} />
            <Text
              style={[styles.selectFieldText, !selectedCamion && styles.selectFieldPlaceholder]}
              numberOfLines={1}
            >
              {selectedCamion ? selectedCamion.immatriculation : 'Aucun camion assigné'}
            </Text>
            <Ionicons name="chevron-down" size={16} color={Colors.slate} />
          </TouchableOpacity>
        </View>

        <Modal
          visible={camionModalVisible}
          animationType="slide"
          transparent
          onRequestClose={() => setCamionModalVisible(false)}
        >
          <View style={styles.modalOverlay}>
            <SafeAreaView style={styles.modalCard} edges={['bottom']}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Sélectionner un camion</Text>
                <TouchableOpacity onPress={() => setCamionModalVisible(false)} style={styles.backBtn}>
                  <Ionicons name="close" size={18} color={Colors.ink} />
                </TouchableOpacity>
              </View>

              <View style={styles.modalSearchBox}>
                <Ionicons name="search-outline" size={16} color={Colors.slate} />
                <TextInput
                  style={styles.modalSearchInput}
                  value={camionSearch}
                  onChangeText={setCamionSearch}
                  placeholder="Rechercher par immatriculation…"
                  placeholderTextColor={Colors.silver}
                  autoFocus
                />
                {camionSearch.length > 0 && (
                  <TouchableOpacity onPress={() => setCamionSearch('')}>
                    <Ionicons name="close-circle" size={16} color={Colors.slate} />
                  </TouchableOpacity>
                )}
              </View>

              <FlatList
                data={filteredCamions}
                keyExtractor={item => String(item.id)}
                keyboardShouldPersistTaps="handled"
                contentContainerStyle={{ paddingBottom: 24 }}
                ListHeaderComponent={
                  <TouchableOpacity style={styles.camionOption} onPress={() => selectCamion(null)}>
                    <View style={styles.camionOptionIcon}>
                      <Ionicons name="close-circle-outline" size={18} color={Colors.slate} />
                    </View>
                    <Text style={styles.camionOptionText}>Aucun camion</Text>
                    {camionId === null && <Ionicons name="checkmark" size={18} color={Colors.navy} />}
                  </TouchableOpacity>
                }
                renderItem={({ item }) => (
                  <TouchableOpacity style={styles.camionOption} onPress={() => selectCamion(item.id)}>
                    <View style={styles.camionOptionIcon}>
                      <Ionicons name="car" size={18} color={Colors.navy} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.camionOptionText}>{item.immatriculation}</Text>
                      <Text style={styles.camionOptionSub}>{item.marque}{item.modele ? ` · ${item.modele}` : ''}</Text>
                    </View>
                    {camionId === item.id && <Ionicons name="checkmark" size={18} color={Colors.navy} />}
                  </TouchableOpacity>
                )}
                ListEmptyComponent={
                  <View style={styles.modalEmpty}>
                    <Text style={styles.modalEmptyText}>Aucun camion ne correspond à « {camionSearch} »</Text>
                  </View>
                }
              />
            </SafeAreaView>
          </View>
        </Modal>

        <Field label="Date d'embauche (AAAA-MM-JJ)" value={dateEmbauche} onChangeText={setDateEmbauche} placeholder="2026-01-15" />
        <Field label="Notes" value={notes} onChangeText={setNotes} placeholder="Observations…" multiline />

        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          {submitting
            ? <ActivityIndicator color={Colors.white} />
            : <Text style={styles.submitBtnText}>{isEdit ? 'Enregistrer' : 'Créer le chauffeur'}</Text>}
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
  placeholder?: string; keyboardType?: 'numeric' | 'phone-pad' | 'email-address'; multiline?: boolean;
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
        autoCapitalize={keyboardType === 'email-address' ? 'none' : 'sentences'}
        multiline={multiline}
        numberOfLines={multiline ? 3 : 1}
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
  inputMultiline: { height: 80, paddingTop: 12, textAlignVertical: 'top' },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderRadius: 999 },
  chipText: { fontSize: 12, fontWeight: '700' },

  selectField: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    height: 48, paddingHorizontal: 14,
    backgroundColor: Colors.white, borderRadius: Radius.md,
    borderWidth: 1, borderColor: Colors.cloud,
  },
  selectFieldText: { flex: 1, fontSize: 14, color: Colors.ink, fontWeight: '600' },
  selectFieldPlaceholder: { color: Colors.silver, fontWeight: '400' },

  modalOverlay: {
    flex: 1, backgroundColor: '#00000055', justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: Colors.paper,
    borderTopLeftRadius: Radius.xl, borderTopRightRadius: Radius.xl,
    maxHeight: '80%', paddingTop: 4,
  },
  modalHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
  },
  modalTitle: { fontSize: 15, fontWeight: '800', color: Colors.ink },
  modalSearchBox: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    height: 44, marginHorizontal: 16, marginBottom: 10, paddingHorizontal: 12,
    backgroundColor: Colors.cloud, borderRadius: Radius.md,
  },
  modalSearchInput: { flex: 1, fontSize: 14, color: Colors.ink },

  camionOption: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: Colors.cloud,
  },
  camionOptionIcon: {
    width: 34, height: 34, borderRadius: 10,
    backgroundColor: Colors.navyTint,
    alignItems: 'center', justifyContent: 'center',
  },
  camionOptionText: { fontSize: 13, fontWeight: '700', color: Colors.ink },
  camionOptionSub:  { fontSize: 11, color: Colors.slate, marginTop: 1 },

  modalEmpty: { padding: 24, alignItems: 'center' },
  modalEmptyText: { fontSize: 12, color: Colors.slate, textAlign: 'center' },

  submitBtn: {
    height: 50, borderRadius: Radius.md, backgroundColor: Colors.navy,
    alignItems: 'center', justifyContent: 'center', marginTop: 12,
  },
  submitBtnDisabled: { backgroundColor: Colors.slate },
  submitBtnText: { color: Colors.white, fontSize: 14, fontWeight: '700' },
});
