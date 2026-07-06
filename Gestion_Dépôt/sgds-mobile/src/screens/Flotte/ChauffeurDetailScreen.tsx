import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { chauffeursApi, Chauffeur } from '../../api/chauffeurs';
import { Colors, Radius } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';
import { useAuth } from '../../context/AuthContext';
import type { FlotteStackParams } from '../../navigation/AppNavigator';

type Nav = NativeStackNavigationProp<FlotteStackParams>;
type Rt  = RouteProp<FlotteStackParams, 'ChauffeurDetail'>;

const STATUT_LABELS: Record<string, string> = {
  ACTIF: 'Actif', INACTIF: 'Inactif', SUSPENDU: 'Suspendu',
};

export function ChauffeurDetailScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<Rt>();
  const { user } = useAuth();
  const perms = user?.permissions ?? {};

  const [chauffeur, setChauffeur] = useState<Chauffeur | null>(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await chauffeursApi.detail(route.params.id);
      setChauffeur(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [route.params.id]);

  useFocusEffect(useCallback(() => { fetchData(); }, [fetchData]));

  const handleDelete = () => {
    if (!chauffeur) return;
    Alert.alert(
      'Supprimer le chauffeur',
      `Voulez-vous vraiment supprimer « ${chauffeur.prenom} ${chauffeur.nom} » ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer', style: 'destructive',
          onPress: async () => {
            try {
              await chauffeursApi.delete(chauffeur.id);
              navigation.goBack();
            } catch (err) {
              Alert.alert('Erreur', getErrorMessage(err));
            }
          },
        },
      ],
    );
  };

  if (loading) return <LoadingSpinner fullScreen message="Chargement du chauffeur..." />;
  if (error || !chauffeur) return <ErrorMessage message={error ?? 'Chauffeur introuvable'} onRetry={fetchData} />;

  const initials = `${chauffeur.prenom[0] ?? ''}${chauffeur.nom[0] ?? ''}`.toUpperCase();

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={20} color={Colors.ink} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>{chauffeur.prenom} {chauffeur.nom}</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.heroCard}>
          <View style={styles.heroAvatar}>
            <Text style={styles.heroAvatarText}>{initials}</Text>
          </View>
          <Text style={styles.heroTitle}>{chauffeur.prenom} {chauffeur.nom}</Text>
          <Text style={styles.heroSub}>{chauffeur.telephone}</Text>
          <View style={styles.statutBadge}>
            <Text style={styles.statutText}>{STATUT_LABELS[chauffeur.statut] ?? chauffeur.statut}</Text>
          </View>
        </View>

        <DetailCard rows={[
          ['N° Permis', chauffeur.numero_permis],
          ['Catégorie permis', chauffeur.categorie_permis],
          ['N° Employé', chauffeur.numero_employe ?? '—'],
          ['Email', chauffeur.email ?? '—'],
          ['Téléphone 2', chauffeur.telephone2 ?? '—'],
          ["Date d'embauche", chauffeur.date_embauche ?? '—'],
          ['Camion assigné', chauffeur.camion_immatriculation ?? 'Aucun'],
        ]} />

        {chauffeur.notes ? (
          <>
            <Text style={styles.sectionTitle}>Notes</Text>
            <View style={styles.notesCard}>
              <Text style={styles.notesText}>{chauffeur.notes}</Text>
            </View>
          </>
        ) : null}

        {(perms.modifier_chauffeur || perms.supprimer_chauffeur) && (
          <View style={styles.actionsRow}>
            {perms.modifier_chauffeur && (
              <TouchableOpacity
                style={[styles.actionBtn, styles.editBtn]}
                onPress={() => navigation.navigate('ChauffeurForm', { id: chauffeur.id })}
              >
                <Ionicons name="create-outline" size={16} color={Colors.white} />
                <Text style={styles.actionBtnText}>Modifier</Text>
              </TouchableOpacity>
            )}
            {perms.supprimer_chauffeur && (
              <TouchableOpacity style={[styles.actionBtn, styles.deleteBtn]} onPress={handleDelete}>
                <Ionicons name="trash-outline" size={16} color={Colors.red} />
                <Text style={[styles.actionBtnText, { color: Colors.red }]}>Supprimer</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function DetailCard({ rows }: { rows: [string, string][] }) {
  return (
    <View style={styles.detailCard}>
      {rows.map(([label, value], i) => (
        <View key={i} style={[styles.detailRow, i < rows.length - 1 && styles.detailRowBorder]}>
          <Text style={styles.detailLabel}>{label}</Text>
          <Text style={styles.detailValue}>{value}</Text>
        </View>
      ))}
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
  headerTitle: { flex: 1, textAlign: 'center', fontSize: 15, fontWeight: '800', color: Colors.ink },

  content: { padding: 16 },

  heroCard: {
    backgroundColor: Colors.white, borderRadius: Radius.lg, padding: 20,
    alignItems: 'center', marginBottom: 16,
    borderWidth: 1, borderColor: Colors.cloud,
  },
  heroAvatar: {
    width: 64, height: 64, borderRadius: 32,
    backgroundColor: Colors.orangeSoft,
    alignItems: 'center', justifyContent: 'center', marginBottom: 12,
  },
  heroAvatarText: { fontSize: 22, fontWeight: '800', color: Colors.orangeDeep },
  heroTitle: { fontSize: 18, fontWeight: '800', color: Colors.ink },
  heroSub:   { fontSize: 13, color: Colors.slate, marginTop: 2, marginBottom: 10 },
  statutBadge: {
    backgroundColor: Colors.navyTint, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999,
  },
  statutText: { fontSize: 11, fontWeight: '700', color: Colors.navy },

  sectionTitle: { fontSize: 13, fontWeight: '800', color: Colors.ink, marginBottom: 8, marginTop: 4 },

  detailCard: {
    backgroundColor: Colors.white, borderRadius: Radius.lg, paddingHorizontal: 16,
    borderWidth: 1, borderColor: Colors.cloud, marginBottom: 16,
  },
  detailRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12 },
  detailRowBorder: { borderBottomWidth: 1, borderBottomColor: Colors.cloud },
  detailLabel: { fontSize: 12, color: Colors.slate, fontWeight: '600' },
  detailValue: { fontSize: 13, color: Colors.ink, fontWeight: '700' },

  notesCard: {
    backgroundColor: Colors.white, borderRadius: Radius.lg, padding: 14,
    borderWidth: 1, borderColor: Colors.cloud, marginBottom: 16,
  },
  notesText: { fontSize: 13, color: Colors.graphite, lineHeight: 19 },

  actionsRow: { flexDirection: 'row', gap: 10, marginTop: 8 },
  actionBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    height: 48, borderRadius: Radius.md,
  },
  editBtn:   { backgroundColor: Colors.navy },
  deleteBtn: { backgroundColor: Colors.redSoft, borderWidth: 1, borderColor: Colors.red + '30' },
  actionBtnText: { fontSize: 13, fontWeight: '700', color: Colors.white },
});
