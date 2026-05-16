import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import dayjs from 'dayjs';

import { mouvementsApi, MouvementDetail } from '../../api/mouvements';
import { Colors, Radius, Spacing, TypeMeta } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';
import { buildMouvementPdf } from '../../utils/pdfTemplate';
import type { MouvementsStackParams } from '../../navigation/AppNavigator';

type Route = RouteProp<MouvementsStackParams, 'MouvementDetail'>;

function fmtN(n: any, dec = 0): string {
  const v = Number(n);
  if (isNaN(v)) return '—';
  return v.toLocaleString('fr-FR', { maximumFractionDigits: dec, minimumFractionDigits: dec });
}

export function MouvementDetailScreen() {
  const navigation = useNavigation();
  const route      = useRoute<Route>();
  const { id }     = route.params;

  const [mvt, setMvt]       = useState<MouvementDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    mouvementsApi.detail(id)
      .then(res => setMvt(res.data))
      .catch(err => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner fullScreen message="Chargement..." />;
  if (error)   return <ErrorMessage message={error} />;
  if (!mvt)    return null;

  const meta    = TypeMeta[mvt.type] ?? { label: mvt.type, color: Colors.slate, soft: Colors.cloud, glyph: '·' };
  const d       = mvt.date ? dayjs(mvt.date) : null;
  const dateStr = d?.isValid() ? d.format('DD/MM/YYYY') : (mvt.date ?? '—');
  const hasTime = !!mvt.date?.includes('T');
  const time    = (d?.isValid() && hasTime) ? d.format('HH:mm') : '';

  const handleExportPdf = async () => {
    try {
      const html = buildMouvementPdf({
        reference:             mvt.reference,
        date:                  mvt.date ?? '',
        type:                  mvt.type,
        produit:               mvt.produit,
        produit_sigle:         mvt.produit_sigle,
        regime:                mvt.regime,
        quantite_ambiant:      mvt.quantite_ambiant,
        quantite_15:           mvt.quantite_15,
        provenance:            mvt.provenance,
        bl_expediteur:         mvt.bl_expediteur,
        bl_client:             mvt.bl_client,
        camion_immatriculation: mvt.camion_immatriculation,
        chauffeur_nom:         mvt.chauffeur_nom,
        destination:           (mvt as any).destination,
        numero_permis_sortie:  mvt.numero_permis_sortie,
        mode_reglement:        mvt.mode_reglement,
        cession_destinataire:  mvt.cession_destinataire,
        cession_motif:         mvt.cession_motif,
        observation:           mvt.observation,
        generatedAt:           dayjs().format('DD/MM/YYYY à HH:mm'),
      });
      const { uri } = await Print.printToFileAsync({ html });
      await Sharing.shareAsync(uri, {
        mimeType: 'application/pdf',
        dialogTitle: `Fiche — ${mvt.reference}`,
        UTI: 'com.adobe.pdf',
      });
    } catch {
      Alert.alert('Erreur', 'Impossible de générer le PDF.');
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 100 }}>
        {/* ── HERO ──────────────────────────────────────────── */}
        <LinearGradient
          colors={[meta.color, meta.color + 'dd']}
          style={styles.hero}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.heroBlob} />

          {/* Nav bar */}
          <View style={styles.heroNav}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.navBtn}>
              <Ionicons name="chevron-back" size={18} color={Colors.white} />
            </TouchableOpacity>
            <View style={styles.navActions}>
              <TouchableOpacity style={styles.navBtn} onPress={handleExportPdf}>
                <Ionicons name="download-outline" size={16} color={Colors.white} />
              </TouchableOpacity>
              <TouchableOpacity style={styles.navBtn}>
                <Ionicons name="ellipsis-horizontal" size={18} color={Colors.white} />
              </TouchableOpacity>
            </View>
          </View>

          {/* Titre */}
          <View style={styles.heroContent}>
            <View style={styles.heroTopRow}>
              <Text style={styles.heroGlyph}>{meta.glyph}</Text>
              <Text style={styles.heroType}>{meta.label}</Text>
              <View style={styles.heroDot} />
              <Text style={styles.heroRef}>{mvt.reference}</Text>
            </View>
            <Text style={styles.heroQte}>
              {fmtN(mvt.quantite_ambiant)}
              <Text style={styles.heroQteUnit}> L</Text>
            </Text>
            <Text style={styles.heroProduit}>
              [{mvt.produit_sigle ?? ''}] {mvt.produit}
            </Text>
            <View style={styles.heroDateRow}>
              <Ionicons name="calendar-outline" size={14} color={Colors.white} />
              <Text style={styles.heroDateText} numberOfLines={1}>{dateStr}</Text>
              {time !== '' && (
                <>
                  <View style={styles.heroDot} />
                  <Ionicons name="time-outline" size={14} color={Colors.white} />
                  <Text style={styles.heroDateText}>{time}</Text>
                </>
              )}
            </View>
          </View>
        </LinearGradient>

        {/* ── QUANTITÉS ─────────────────────────────────────── */}
        <View style={styles.pad}>
          <View style={styles.qteCard}>
            <View style={styles.qteBox}>
              <Text style={styles.qteLabel}>AMBIANT</Text>
              <Text style={[styles.qteValue, { color: meta.color }]}>{fmtN(mvt.quantite_ambiant)}</Text>
              <Text style={styles.qteUnit}>litres</Text>
            </View>
            <View style={styles.qteDivider} />
            <View style={styles.qteBox}>
              <Text style={styles.qteLabel}>15°C</Text>
              <Text style={[styles.qteValue, { color: meta.color }]}>{fmtN(mvt.quantite_15)}</Text>
              <Text style={styles.qteUnit}>litres</Text>
            </View>
          </View>
        </View>

        {/* ── INFORMATIONS ──────────────────────────────────── */}
        <SectionHeader title="Informations" />
        <View style={styles.pad}>
          <DetailCard rows={[
            ['Régime',      mvt.regime],
            ['Référence',   mvt.reference],
            ['Destination', (mvt as any).destination ?? (mvt as any).provenance],
            ['Observation', mvt.observation ?? null],
          ]} />
        </View>

        {/* Détails spécifiques ENTREE */}
        {mvt.type === 'ENTREE' && (
          <>
            <SectionHeader title="Logistique" />
            <View style={styles.pad}>
              <DetailCard rows={[
                ['Provenance',     mvt.provenance],
                ['BL Expéditeur',  mvt.bl_expediteur],
                ['BL Client',      mvt.bl_client],
                ['Camion',         mvt.camion_immatriculation],
                ['Chauffeur',      mvt.chauffeur_nom],
              ]} />
            </View>
          </>
        )}

        {mvt.type === 'SORTIE' && (
          <>
            <SectionHeader title="Logistique" />
            <View style={styles.pad}>
              <DetailCard rows={[
                ['Destination',     (mvt as any).destination],
                ['N° Permis',        mvt.numero_permis_sortie],
                ['Mode règlement',   mvt.mode_reglement],
                ['Camion',           mvt.camion_immatriculation],
                ['Chauffeur',        mvt.chauffeur_nom],
              ]} />
            </View>
          </>
        )}

        {mvt.type === 'CESSION' && (
          <>
            <SectionHeader title="Cession" />
            <View style={styles.pad}>
              <DetailCard rows={[
                ['Destinataire', mvt.cession_destinataire],
                ['Motif',        mvt.cession_motif],
              ]} />
            </View>
          </>
        )}

        {/* ── SUIVI ─────────────────────────────────────────── */}
        <SectionHeader title="Suivi" />
        <View style={styles.pad}>
          <View style={styles.timelineCard}>
            {[
              { label: 'Saisie initiale',          sub: `${dateStr} · ${time}`, done: true },
              { label: 'Validation responsable',   sub: mvt.produit ?? 'Responsable dépôt',   done: true },
              { label: 'Comptabilisation',         sub: 'En attente de clôture',              done: false },
            ].map((step, i, arr) => (
              <View key={i} style={styles.timelineItem}>
                <View style={styles.timelineTrack}>
                  <View style={[
                    styles.timelineDot,
                    step.done
                      ? { backgroundColor: meta.color }
                      : { borderWidth: 2, borderColor: Colors.mist, backgroundColor: 'transparent' },
                  ]}>
                    {step.done && <Ionicons name="checkmark" size={11} color={Colors.white} />}
                  </View>
                  {i < arr.length - 1 && (
                    <View style={[
                      styles.timelineLine,
                      { backgroundColor: step.done ? meta.color + '44' : Colors.cloud },
                    ]} />
                  )}
                </View>
                <View style={styles.timelineBody}>
                  <Text style={[styles.timelineLabel, !step.done && { color: Colors.slate }]}>
                    {step.label}
                  </Text>
                  <Text style={styles.timelineSub}>{step.sub}</Text>
                </View>
              </View>
            ))}
          </View>
        </View>
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

function DetailCard({ rows }: { rows: [string, string | null | undefined][] }) {
  const filtered = rows.filter(r => r[1] != null && r[1] !== '');
  if (filtered.length === 0) return null;
  return (
    <View style={styles.detailCard}>
      {filtered.map(([label, value], i) => (
        <View
          key={i}
          style={[styles.detailRow, i < filtered.length - 1 && styles.detailRowBorder]}
        >
          <Text style={styles.detailLabel}>{label}</Text>
          <Text style={styles.detailValue}>{value}</Text>
        </View>
      ))}
    </View>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },

  // Hero
  hero: {
    paddingTop: 14, paddingHorizontal: 16, paddingBottom: 24,
    position: 'relative', overflow: 'hidden',
  },
  heroBlob: {
    position: 'absolute', top: -40, right: -40,
    width: 160, height: 160, borderRadius: 80,
    backgroundColor: Colors.white + '1a',
  },
  heroNav: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 18,
  },
  navBtn: {
    width: 34, height: 34, borderRadius: 10,
    backgroundColor: Colors.white + '26',
    alignItems: 'center', justifyContent: 'center',
  },
  navActions: { flexDirection: 'row', gap: 8 },
  heroContent: {},
  heroTopRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 },
  heroGlyph: { color: Colors.white + 'cc', fontSize: 14, fontWeight: '800' },
  heroType:  { color: Colors.white + 'cc', fontSize: 11, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  heroDot:   { width: 3, height: 3, borderRadius: 1.5, backgroundColor: Colors.white + '80' },
  heroRef:   { color: Colors.white + 'cc', fontSize: 11 },
  heroQte:   { color: Colors.white, fontSize: 30, fontWeight: '800', letterSpacing: -0.5 },
  heroQteUnit: { fontSize: 14, fontWeight: '600', opacity: 0.8 },
  heroProduit: { color: Colors.white + 'cc', fontSize: 13, marginTop: 2 },
  heroDateRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 14 },
  heroDateText: { color: Colors.white + 'cc', fontSize: 12, textTransform: 'capitalize' },

  // Quantités
  pad: { paddingHorizontal: 16, paddingTop: 16 },
  qteCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg, padding: 0,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 4,
    flexDirection: 'row', overflow: 'hidden',
  },
  qteBox: {
    flex: 1, padding: 14, backgroundColor: Colors.cloud,
    alignItems: 'center', gap: 4,
  },
  qteDivider: { width: 1, backgroundColor: Colors.mist },
  qteLabel: {
    fontSize: 10, fontWeight: '700', color: Colors.slate,
    letterSpacing: 0.5, textTransform: 'uppercase',
  },
  qteValue: { fontSize: 18, fontWeight: '800' },
  qteUnit:  { fontSize: 10, color: Colors.slate },

  // Section header
  sectionHeader: { paddingHorizontal: 20, paddingTop: 22, paddingBottom: 10 },
  sectionTitle:  { fontSize: 14, fontWeight: '800', color: Colors.ink, letterSpacing: -0.2 },

  // Detail card
  detailCard: {
    backgroundColor: Colors.white, borderRadius: Radius.lg,
    paddingHorizontal: 16,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  detailRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'flex-start', gap: 12,
    paddingVertical: 12,
  },
  detailRowBorder: { borderBottomWidth: 1, borderBottomColor: Colors.cloud },
  detailLabel: { fontSize: 11, color: Colors.slate, fontWeight: '600', letterSpacing: 0.2 },
  detailValue: { fontSize: 13, color: Colors.ink, fontWeight: '600', textAlign: 'right', flex: 1 },

  // Timeline
  timelineCard: {
    backgroundColor: Colors.white, borderRadius: Radius.lg,
    padding: 16,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  timelineItem:  { flexDirection: 'row', gap: 12 },
  timelineTrack: { alignItems: 'center', flexShrink: 0 },
  timelineDot: {
    width: 18, height: 18, borderRadius: 9,
    alignItems: 'center', justifyContent: 'center',
  },
  timelineLine: { width: 2, flex: 1, marginTop: 2 },
  timelineBody: { flex: 1, paddingBottom: 14 },
  timelineLabel: { fontSize: 13, fontWeight: '700', color: Colors.ink },
  timelineSub:   { fontSize: 11, color: Colors.slate, marginTop: 1 },
});
