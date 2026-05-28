/**
 * MouvementDetailScreen — Refonte "Bordereau officiel" (Variant A)
 *
 * Remplace l'ancien écran détail avec :
 *   • Top nav navy : référence en monospace + badge statut VALIDÉ/EN ATTENTE
 *   • Bandeau coloré selon le type (Entrée vert / Sortie rouge / Cession violet)
 *   • Sections numérotées 01-04 style document officiel
 *   • Table Ambiant vs 15°C avec la valeur ambiant en grand et colorée
 *   • Section transport sur 2 cartes côte à côte (Camion / Chauffeur)
 *   • Section signatures (Saisi par / Validé par)
 *   • Action bar collante en bas : IMPRIMER + Télécharger + Partager
 */
import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import dayjs from 'dayjs';

import { mouvementsApi, MouvementDetail } from '../../api/mouvements';
import { Colors, TypeMeta } from '../../constants/colors';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { getErrorMessage } from '../../utils/format';
import { buildMouvementPdf } from '../../utils/pdfTemplate';
import type { MouvementsStackParams } from '../../navigation/AppNavigator';

type Route = RouteProp<MouvementsStackParams, 'MouvementDetail'>;

// ── Helpers ───────────────────────────────────────────────────────

function fmtN(n: any): string {
  const v = Number(n);
  if (isNaN(v)) return '—';
  return v.toLocaleString('fr-FR', { maximumFractionDigits: 0 });
}

function fmtDate(iso?: string | null): string {
  if (!iso) return '—';
  const d = dayjs(iso);
  return d.isValid()
    ? d.format('DD MMMM YYYY').replace(/^./, c => c.toUpperCase())
    : '—';
}

function fmtTime(iso?: string | null): string {
  if (!iso || !iso.includes('T')) return '';
  const d = dayjs(iso);
  return d.isValid() ? d.format('HH:mm') : '';
}

const typeIcon = (type: string): any => {
  if (type === 'ENTREE') return 'arrow-down';
  if (type === 'SORTIE') return 'arrow-up';
  if (type === 'CESSION') return 'swap-horizontal';
  return 'checkmark';
};

// ── Composant principal ───────────────────────────────────────────

export function MouvementDetailScreen() {
  const navigation = useNavigation();
  const route      = useRoute<Route>();
  const { id }     = route.params;

  const [mvt, setMvt]                     = useState<MouvementDetail | null>(null);
  const [loading, setLoading]             = useState(true);
  const [error, setError]                 = useState<string | null>(null);
  const [generatingPdf, setGeneratingPdf] = useState(false);

  useEffect(() => {
    mouvementsApi.detail(id)
      .then(res => setMvt(res.data))
      .catch(err => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner fullScreen message="Chargement..." />;
  if (error)   return <ErrorMessage message={error} />;
  if (!mvt)    return null;

  const meta   = TypeMeta[mvt.type] ?? {
    label: mvt.type, color: Colors.slate, soft: Colors.cloud, glyph: '·',
  };
  const statut   = (mvt as any).statut ?? ((mvt as any).valide_par ? 'VALIDÉ' : 'EN ATTENTE');
  const isValide = statut === 'VALIDÉ';

  // ── Génération PDF ───────────────────────────────────────────────

  const buildHtml = () => buildMouvementPdf({
    reference:              mvt.reference,
    date:                   mvt.date ?? '',
    type:                   mvt.type,
    produit:                mvt.produit,
    produit_sigle:          mvt.produit_sigle,
    regime:                 mvt.regime,
    quantite_ambiant:       mvt.quantite_ambiant,
    quantite_15:            mvt.quantite_15,
    provenance:             mvt.provenance,
    bl_expediteur:          mvt.bl_expediteur,
    bl_client:              mvt.bl_client,
    camion_immatriculation: mvt.camion_immatriculation,
    chauffeur_nom:          mvt.chauffeur_nom,
    destination:            mvt.destination,
    numero_permis_sortie:   mvt.numero_permis_sortie,
    mode_reglement:         mvt.mode_reglement,
    cession_destinataire:   mvt.cession_destinataire,
    cession_motif:          mvt.cession_motif,
    observation:            mvt.observation,
    generatedAt:            dayjs().format('DD/MM/YYYY à HH:mm'),
  });

  const handlePrint = async () => {
    setGeneratingPdf(true);
    try {
      await Print.printAsync({ html: buildHtml() });
    } catch {
      // L'utilisateur a annulé volontairement — pas d'alerte
    } finally {
      setGeneratingPdf(false);
    }
  };

  const handleDownload = async () => {
    setGeneratingPdf(true);
    try {
      const { uri } = await Print.printToFileAsync({ html: buildHtml() });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, {
          mimeType: 'application/pdf',
          dialogTitle: `Enregistrer ${mvt.reference}.pdf`,
          UTI: 'com.adobe.pdf',
        });
      } else {
        Alert.alert('PDF généré', `Fichier créé : ${mvt.reference}.pdf`);
      }
    } catch {
      Alert.alert('Erreur', 'Impossible de générer le PDF.');
    } finally {
      setGeneratingPdf(false);
    }
  };

  const handleShare = async () => {
    setGeneratingPdf(true);
    try {
      const { uri } = await Print.printToFileAsync({ html: buildHtml() });
      await Sharing.shareAsync(uri, {
        mimeType: 'application/pdf',
        dialogTitle: `Partager — ${mvt.reference}`,
        UTI: 'com.adobe.pdf',
      });
    } catch {
      Alert.alert('Erreur', 'Impossible de partager le document.');
    } finally {
      setGeneratingPdf(false);
    }
  };

  // ── Logistique : lignes conditionnelles ─────────────────────────

  type KVRow = { label: string; value: string; icon?: any; mono?: boolean };

  const logistiqueRows: KVRow[] = [
    mvt.provenance           ? { label: 'Provenance',       value: mvt.provenance,           icon: 'business-outline' } : null,
    mvt.destination          ? { label: 'Destination',      value: mvt.destination,           icon: 'location-outline' } : null,
    mvt.cession_destinataire ? { label: 'Destinataire',     value: mvt.cession_destinataire,  icon: 'location-outline' } : null,
    mvt.bl_expediteur        ? { label: 'BL Expéditeur',    value: mvt.bl_expediteur,          mono: true }             : null,
    mvt.bl_client            ? { label: 'BL Client',        value: mvt.bl_client,              mono: true }             : null,
    mvt.numero_permis_sortie ? { label: 'N° Permis sortie', value: mvt.numero_permis_sortie,   mono: true }             : null,
    mvt.mode_reglement       ? { label: 'Mode règlement',   value: mvt.mode_reglement }                                  : null,
    mvt.cession_motif        ? { label: 'Motif',            value: mvt.cession_motif }                                   : null,
  ].filter(Boolean) as KVRow[];

  const hasTransport  = !!(mvt.camion_immatriculation || mvt.chauffeur_nom);
  const hasLogistique = logistiqueRows.length > 0;

  // ── Rendu ────────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 120 }}
      >
        {/* ─────────────────── TOP NAV (navy) ─────────────────── */}
        <View style={styles.topNav}>
          <View style={styles.topNavRow}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.navBtn}>
              <Ionicons name="chevron-back" size={18} color={Colors.white} />
            </TouchableOpacity>
            <View style={styles.topNavCenter}>
              <Text style={styles.topNavTitle}>Bordereau</Text>
              <Text style={styles.topNavSub}>FICHE MOUVEMENT</Text>
            </View>
            <TouchableOpacity style={styles.navBtn}>
              <Ionicons name="ellipsis-horizontal" size={18} color={Colors.white} />
            </TouchableOpacity>
          </View>

          <View style={styles.refRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.refLabel}>RÉFÉRENCE</Text>
              <Text style={styles.refValue}>{mvt.reference}</Text>
            </View>
            <View style={[
              styles.statutBadge,
              { backgroundColor: isValide ? Colors.green : Colors.amber },
            ]}>
              {isValide && (
                <Ionicons name="checkmark" size={12} color={Colors.white} style={{ marginRight: 4 }} />
              )}
              <Text style={styles.statutText}>{statut}</Text>
            </View>
          </View>
        </View>

        {/* ─────────────── BANDEAU TYPE (couleur) ─────────────── */}
        <View style={[styles.typeBanner, { backgroundColor: meta.color }]}>
          <View style={styles.typeBannerIcon}>
            <Ionicons name={typeIcon(mvt.type)} size={16} color={Colors.white} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.typeBannerLabel}>TYPE DE MOUVEMENT</Text>
            <Text style={styles.typeBannerTitle} numberOfLines={1}>
              {meta.label.toUpperCase()} · {mvt.regime}
            </Text>
          </View>
        </View>

        {/* ─────────────── BODY ─────────────── */}
        <View style={styles.body}>

          {/* Section 01 — Produit & quantités */}
          <Section num="01" title="Produit & quantités">
            <View style={styles.produitRow}>
              <View style={styles.sigleBox}>
                <Text style={styles.sigleText}>{mvt.produit_sigle}</Text>
              </View>
              <View>
                <Text style={styles.miniLabel}>PRODUIT</Text>
                <Text style={styles.produitName}>{mvt.produit}</Text>
              </View>
            </View>

            <View style={styles.qteTable}>
              <View style={styles.qteHeader}>
                <Text style={styles.qteHeaderCell}>QTÉ AMBIANT</Text>
                <Text style={[styles.qteHeaderCell, { textAlign: 'right' }]}>QTÉ 15°C</Text>
              </View>
              <View style={styles.qteValues}>
                <Text style={[styles.qteValueBig, { color: meta.color }]}>
                  {fmtN(mvt.quantite_ambiant)}
                  <Text style={styles.qteUnit}> L</Text>
                </Text>
                <Text style={styles.qteValue15}>
                  {fmtN(mvt.quantite_15)}
                  <Text style={styles.qteUnit}> L</Text>
                </Text>
              </View>
            </View>
          </Section>

          {/* Section 02 — Logistique (conditionnelle) */}
          {hasLogistique && (
            <Section num="02" title="Logistique">
              <KeyValTable rows={logistiqueRows} />
            </Section>
          )}

          {/* Section 03 — Transport (conditionnelle) */}
          {hasTransport && (
            <Section num="03" title="Transport">
              <View style={styles.transportRow}>
                {mvt.camion_immatriculation && (
                  <View style={styles.transportCard}>
                    <View style={styles.transportHeader}>
                      <Ionicons name="car-outline" size={14} color={Colors.navy} />
                      <Text style={styles.transportLabel}>CAMION</Text>
                    </View>
                    <Text style={[styles.transportValue, styles.monoText]}>
                      {mvt.camion_immatriculation}
                    </Text>
                  </View>
                )}
                {mvt.chauffeur_nom && (
                  <View style={styles.transportCard}>
                    <View style={styles.transportHeader}>
                      <Ionicons name="person-outline" size={14} color={Colors.navy} />
                      <Text style={styles.transportLabel}>CHAUFFEUR</Text>
                    </View>
                    <Text style={styles.transportValue}>{mvt.chauffeur_nom}</Text>
                  </View>
                )}
              </View>
            </Section>
          )}

          {/* Section 04 — Émission & validation */}
          <Section num="04" title="Émission & validation">
            <View style={styles.signCard}>
              <View style={styles.dateRow}>
                <Ionicons name="calendar-outline" size={14} color={Colors.slate} />
                <Text style={styles.dateText}>{fmtDate(mvt.date)}</Text>
                {!!fmtTime(mvt.date) && (
                  <>
                    <Text style={styles.dot}>•</Text>
                    <Ionicons name="time-outline" size={13} color={Colors.slate} />
                    <Text style={styles.dateText}>{fmtTime(mvt.date)}</Text>
                  </>
                )}
              </View>
              <View style={styles.signDivider} />
              <View style={styles.signRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.signLabel}>SAISI PAR</Text>
                  <Text style={styles.signValue}>{(mvt as any).saisi_par ?? '—'}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.signLabel}>VALIDÉ PAR</Text>
                  <Text style={[
                    styles.signValue,
                    !(mvt as any).valide_par && { color: Colors.silver },
                  ]}>
                    {(mvt as any).valide_par ?? 'En attente'}
                  </Text>
                </View>
              </View>
            </View>
          </Section>

          {/* Observation */}
          {!!mvt.observation && (
            <View style={styles.observation}>
              <Ionicons name="information-circle-outline" size={16} color={Colors.amber} />
              <View style={{ flex: 1 }}>
                <Text style={styles.obsLabel}>OBSERVATION</Text>
                <Text style={styles.obsText}>{mvt.observation}</Text>
              </View>
            </View>
          )}
        </View>
      </ScrollView>

      {/* ─────────────── ACTION BAR STICKY ─────────────── */}
      <View style={styles.actionBar}>
        <TouchableOpacity
          style={[styles.printBtn, generatingPdf && { opacity: 0.6 }]}
          onPress={handlePrint}
          disabled={generatingPdf}
          activeOpacity={0.8}
        >
          {generatingPdf
            ? <ActivityIndicator size="small" color={Colors.white} />
            : <Ionicons name="print-outline" size={18} color={Colors.white} />
          }
          <Text style={styles.printBtnText}>Imprimer</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.iconAction, generatingPdf && { opacity: 0.6 }]}
          onPress={handleDownload}
          disabled={generatingPdf}
          activeOpacity={0.7}
        >
          <Ionicons name="download-outline" size={20} color={Colors.navy} />
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.iconAction, generatingPdf && { opacity: 0.6 }]}
          onPress={handleShare}
          disabled={generatingPdf}
          activeOpacity={0.7}
        >
          <Ionicons name="share-outline" size={20} color={Colors.navy} />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// ── Sous-composants ───────────────────────────────────────────────

function Section({
  num, title, children,
}: { num: string; title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionNum}>{num}</Text>
        <Text style={styles.sectionTitle}>{title}</Text>
        <View style={styles.sectionLine} />
      </View>
      {children}
    </View>
  );
}

type KVRow = { label: string; value: string; icon?: any; mono?: boolean };

function KeyValTable({ rows }: { rows: KVRow[] }) {
  return (
    <View style={styles.kvTable}>
      {rows.map((r, i) => (
        <View
          key={i}
          style={[styles.kvRow, i < rows.length - 1 && styles.kvRowBorder]}
        >
          {r.icon && <Ionicons name={r.icon} size={14} color={Colors.slate} />}
          <Text style={styles.kvLabel} numberOfLines={1}>{r.label}</Text>
          <Text style={[styles.kvValue, r.mono && styles.monoText]} numberOfLines={2}>
            {r.value}
          </Text>
        </View>
      ))}
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },

  // ── Top nav (navy) ─────────────────────────
  topNav: {
    backgroundColor: Colors.navy,
    paddingHorizontal: 16, paddingTop: 4, paddingBottom: 18,
  },
  topNavRow: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 14,
  },
  navBtn: {
    width: 34, height: 34, borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center', justifyContent: 'center',
  },
  topNavCenter: { alignItems: 'center', flex: 1 },
  topNavTitle: { color: Colors.white, fontSize: 13, fontWeight: '700' },
  topNavSub: {
    color: 'rgba(255,255,255,0.5)', fontSize: 10, fontWeight: '600', letterSpacing: 0.5,
  },

  refRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12,
  },
  refLabel: {
    color: 'rgba(255,255,255,0.5)', fontSize: 9, fontWeight: '700', letterSpacing: 1.2, marginBottom: 4,
  },
  refValue: {
    color: Colors.white, fontSize: 18, fontWeight: '800', letterSpacing: 0.5,
    fontFamily: 'Menlo',
  },
  statutBadge: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999,
  },
  statutText: { color: Colors.white, fontSize: 10, fontWeight: '800', letterSpacing: 0.5 },

  // ── Bandeau type ─────────────────────────────
  typeBanner: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingVertical: 10, paddingHorizontal: 16,
  },
  typeBannerIcon: {
    width: 30, height: 30, borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center', justifyContent: 'center',
  },
  typeBannerLabel: {
    color: 'rgba(255,255,255,0.6)', fontSize: 9, fontWeight: '700', letterSpacing: 1,
  },
  typeBannerTitle: { color: Colors.white, fontSize: 15, fontWeight: '800', letterSpacing: -0.2 },

  // ── Body ─────────────────────────────────────
  body: { paddingHorizontal: 14, paddingTop: 14 },

  section: { marginBottom: 16 },
  sectionHeader: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    marginBottom: 10, paddingHorizontal: 4,
  },
  sectionNum: {
    fontSize: 9, fontWeight: '800', color: Colors.orange, letterSpacing: 1,
    fontFamily: 'Menlo',
  },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: Colors.ink, letterSpacing: -0.2 },
  sectionLine:  { flex: 1, height: 1, backgroundColor: Colors.mist, marginLeft: 4 },

  // Produit
  produitRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14 },
  sigleBox: {
    width: 42, height: 42, borderRadius: 10,
    backgroundColor: Colors.navyTint,
    alignItems: 'center', justifyContent: 'center',
  },
  sigleText:   { fontSize: 11, fontWeight: '800', color: Colors.navy },
  miniLabel:   { fontSize: 9, color: Colors.slate, fontWeight: '700', letterSpacing: 0.8 },
  produitName: { fontSize: 15, fontWeight: '700', color: Colors.ink },

  // Quantité table
  qteTable: {
    borderWidth: 1, borderColor: Colors.mist, borderRadius: 10, overflow: 'hidden',
  },
  qteHeader: {
    flexDirection: 'row', backgroundColor: Colors.cloud,
    paddingHorizontal: 12, paddingVertical: 8,
  },
  qteHeaderCell: {
    flex: 1, fontSize: 9, fontWeight: '800', color: Colors.slate, letterSpacing: 0.8,
  },
  qteValues: {
    flexDirection: 'row', paddingHorizontal: 12, paddingVertical: 12,
    justifyContent: 'space-between',
  },
  qteValueBig: { fontSize: 26, fontWeight: '800', letterSpacing: -0.5 },
  qteValue15:  { fontSize: 22, fontWeight: '700', color: Colors.graphite, letterSpacing: -0.5, textAlign: 'right' },
  qteUnit:     { fontSize: 12, color: Colors.slate, fontWeight: '600' },

  // Key/Val table
  kvTable: {
    backgroundColor: Colors.white,
    borderWidth: 1, borderColor: Colors.mist, borderRadius: 10, overflow: 'hidden',
  },
  kvRow: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingHorizontal: 12, paddingVertical: 10,
  },
  kvRowBorder: { borderBottomWidth: 1, borderBottomColor: Colors.cloud },
  kvLabel: {
    fontSize: 11, color: Colors.slate, fontWeight: '600', width: 110, flexShrink: 0,
  },
  kvValue: { flex: 1, fontSize: 12, color: Colors.ink, fontWeight: '700', textAlign: 'right' },

  // Transport
  transportRow: { flexDirection: 'row', gap: 8 },
  transportCard: {
    flex: 1, backgroundColor: Colors.white,
    borderWidth: 1, borderColor: Colors.mist, borderRadius: 10, padding: 12,
  },
  transportHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 },
  transportLabel:  { fontSize: 9, fontWeight: '800', color: Colors.slate, letterSpacing: 0.8 },
  transportValue:  { fontSize: 13, fontWeight: '700', color: Colors.ink },

  // Signatures
  signCard: {
    backgroundColor: Colors.white,
    borderWidth: 1, borderColor: Colors.mist, borderRadius: 10, padding: 12,
  },
  dateRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  dateText: { fontSize: 13, color: Colors.ink, fontWeight: '600' },
  dot:      { color: Colors.mist },
  signDivider: { height: 1, backgroundColor: Colors.cloud, marginVertical: 10 },
  signRow:  { flexDirection: 'row', gap: 16 },
  signLabel: {
    fontSize: 9, color: Colors.slate, fontWeight: '700', letterSpacing: 0.6, marginBottom: 2,
  },
  signValue: { fontSize: 12, color: Colors.ink, fontWeight: '700' },

  // Observation
  observation: {
    flexDirection: 'row', gap: 10,
    backgroundColor: Colors.amberSoft,
    borderWidth: 1, borderColor: Colors.amber + '40',
    borderRadius: 10, padding: 12, marginTop: 4,
  },
  obsLabel: {
    fontSize: 9, color: Colors.amber, fontWeight: '800', letterSpacing: 0.8, marginBottom: 3,
  },
  obsText: { fontSize: 12, color: Colors.graphite, lineHeight: 18 },

  // ── Action bar sticky ──────────────────────
  actionBar: {
    position: 'absolute', left: 0, right: 0, bottom: 0,
    backgroundColor: Colors.white,
    borderTopWidth: 1, borderTopColor: Colors.mist,
    paddingHorizontal: 14, paddingTop: 12, paddingBottom: 28,
    flexDirection: 'row', alignItems: 'center', gap: 8,
  },
  printBtn: {
    flex: 1, height: 46, borderRadius: 12,
    backgroundColor: Colors.navy,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
  },
  printBtnText: { color: Colors.white, fontSize: 14, fontWeight: '800', letterSpacing: -0.2 },
  iconAction: {
    width: 46, height: 46, borderRadius: 12,
    backgroundColor: Colors.cloud,
    alignItems: 'center', justifyContent: 'center',
  },

  monoText: { fontFamily: 'Menlo', letterSpacing: 0.3 },
});
