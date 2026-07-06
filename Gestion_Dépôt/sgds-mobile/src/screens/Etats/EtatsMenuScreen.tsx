import React from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { EtatsStackParams } from '../../navigation/AppNavigator';
import { Colors } from '../../constants/colors';

type Nav = NativeStackNavigationProp<EtatsStackParams>;

const ETATS = [
  {
    key:   'CarteStock',
    icon:  'layers-outline',
    color: Colors.navy,
    soft:  Colors.navyTint,
    title: 'Carte de Stock',
    desc:  'Évolution du stock produit par produit avec le détail de chaque mouvement.',
    tag:   'ÉTAT',
  },
  {
    key:   'RecapMouvements',
    icon:  'bar-chart-outline',
    color: Colors.entree,
    soft:  Colors.greenSoft,
    title: 'Récapitulatif',
    desc:  'Synthèse globale des entrées, sorties et cessions par produit.',
    tag:   'RAPPORT',
  },
  {
    key:   'StockOuverture',
    icon:  'git-compare-outline',
    color: '#0E7490',
    soft:  '#CFFAFE',
    title: 'Stock Ambiant',
    desc:  'Stock d\'ouverture et de fermeture ambiant par produit pour chaque période comptable.',
    tag:   'PÉRIODE',
  },
  {
    key:   'Stock15',
    icon:  'thermometer-outline',
    color: '#0E7490',
    soft:  '#CFFAFE',
    title: 'Stock à 15°C',
    desc:  'Stock d\'ouverture et de fermeture corrigé à 15°C par produit pour chaque période comptable.',
    tag:   'PÉRIODE',
  },
  {
    key:   'FraisPassage',
    icon:  'pricetag-outline',
    color: '#92400E',
    soft:  '#FEF3C7',
    title: 'Frais de Passage',
    desc:  'Tarifs de passage en vigueur par produit (FCFA/litre).',
    tag:   'TARIF',
  },
  {
    key:   'Coulage',
    icon:  'analytics-outline',
    color: '#5B21B6',
    soft:  '#EDE9FE',
    title: 'Coulage Marketeurs',
    desc:  'Analyse des pertes de coulage par période clôturée : entrées, sorties, montants.',
    tag:   'COULAGE',
  },
] as const;

export function EtatsMenuScreen() {
  const navigation = useNavigation<Nav>();

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <LinearGradient
        colors={[Colors.navySoft, Colors.navy, Colors.navyDeep]}
        style={styles.hero}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.heroBlob} />
        <View style={styles.heroRow}>
          <View>
            <Text style={styles.heroSub}>Rapports</Text>
            <Text style={styles.heroTitle}>États Marketeur</Text>
          </View>
          <View style={styles.heroIcon}>
            <Ionicons name="document-text" size={24} color={Colors.white} />
          </View>
        </View>
        <Text style={styles.heroDesc}>
          Consultez et exportez vos états de stock et récapitulatifs de mouvements en PDF.
        </Text>
      </LinearGradient>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.sectionLabel}>Choisir un état</Text>

        {ETATS.map((e) => (
          <TouchableOpacity
            key={e.key}
            style={styles.card}
            onPress={() => navigation.navigate(e.key as any)}
            activeOpacity={0.75}
          >
            {/* Icône */}
            <View style={[styles.cardIcon, { backgroundColor: e.soft }]}>
              <Ionicons name={e.icon as any} size={28} color={e.color} />
            </View>

            {/* Texte */}
            <View style={styles.cardBody}>
              <View style={styles.cardTop}>
                <Text style={styles.cardTitle}>{e.title}</Text>
                <View style={[styles.tagBadge, { backgroundColor: e.soft }]}>
                  <Text style={[styles.tagText, { color: e.color }]}>{e.tag}</Text>
                </View>
              </View>
              <Text style={styles.cardDesc}>{e.desc}</Text>
            </View>

            {/* Chevron */}
            <View style={styles.cardChev}>
              <Ionicons name="chevron-forward" size={18} color={Colors.silver} />
            </View>
          </TouchableOpacity>
        ))}

        {/* Info bloc */}
        <View style={styles.infoBanner}>
          <Ionicons name="print-outline" size={18} color={Colors.navy} />
          <Text style={styles.infoText}>
            Chaque état peut être imprimé ou partagé en PDF directement depuis votre téléphone.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:  { flex: 1, backgroundColor: Colors.paper },
  scroll: { flex: 1 },
  content: { padding: 16, paddingBottom: 40 },

  // Hero
  hero: {
    paddingHorizontal: 20, paddingTop: 16, paddingBottom: 28,
    overflow: 'hidden',
  },
  heroBlob: {
    position: 'absolute', right: -40, top: -40,
    width: 160, height: 160, borderRadius: 80,
    backgroundColor: Colors.orange + '1f',
  },
  heroRow: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 10,
  },
  heroSub:   { color: Colors.white + 'bf', fontSize: 11, fontWeight: '600', letterSpacing: 0.5 },
  heroTitle: { color: Colors.white, fontSize: 22, fontWeight: '800', letterSpacing: -0.5, marginTop: 2 },
  heroIcon: {
    width: 48, height: 48, borderRadius: 14,
    backgroundColor: Colors.white + '1a',
    alignItems: 'center', justifyContent: 'center',
  },
  heroDesc: { color: Colors.white + 'b3', fontSize: 12, lineHeight: 18 },

  sectionLabel: {
    fontSize: 11, fontWeight: '800', color: Colors.slate,
    textTransform: 'uppercase', letterSpacing: 0.6,
    marginBottom: 12, marginTop: 4,
  },

  // Cards
  card: {
    backgroundColor: Colors.white,
    borderRadius: 18, padding: 16,
    flexDirection: 'row', alignItems: 'center',
    marginBottom: 12,
    borderWidth: 1, borderColor: Colors.cloud,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 6, elevation: 2,
  },
  cardIcon: {
    width: 60, height: 60, borderRadius: 16,
    alignItems: 'center', justifyContent: 'center',
    marginRight: 14,
  },
  cardBody: { flex: 1 },
  cardTop: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
  cardTitle: { fontSize: 15, fontWeight: '800', color: Colors.ink },
  tagBadge: { paddingHorizontal: 7, paddingVertical: 2, borderRadius: 6 },
  tagText:  { fontSize: 9, fontWeight: '700', letterSpacing: 0.5 },
  cardDesc: { fontSize: 11, color: Colors.slate, lineHeight: 16 },
  cardChev: { marginLeft: 8 },

  // Info
  infoBanner: {
    backgroundColor: Colors.navyTint,
    borderRadius: 14, padding: 14,
    flexDirection: 'row', alignItems: 'flex-start',
    gap: 10, marginTop: 8,
    borderWidth: 1, borderColor: Colors.navy + '20',
  },
  infoText: { flex: 1, fontSize: 12, color: Colors.navy, lineHeight: 18 },
});
