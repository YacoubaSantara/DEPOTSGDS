import React from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { Colors, Radius } from '../../constants/colors';

const LAST_UPDATE = '16 mai 2026';

interface Section {
  title: string;
  body: string;
}

const SECTIONS: Section[] = [
  {
    title: '1. Objet et acceptation',
    body: `Les présentes Conditions Générales d'Utilisation (CGU) régissent l'accès et l'utilisation de l'application mobile SGDS (Système de Gestion des Dépôts pétroliers), éditée par SANKE.

En accédant à l'application, l'utilisateur reconnaît avoir pris connaissance des présentes conditions et les accepte sans réserve. Toute utilisation de l'application implique l'acceptation pleine et entière des présentes CGU.`,
  },
  {
    title: '2. Description du service',
    body: `SGDS est une application professionnelle destinée à la gestion des dépôts pétroliers. Elle permet aux utilisateurs autorisés (marketeurs, responsables dépôt, opérateurs) de :

• Consulter et enregistrer les mouvements de produits pétroliers (entrées, sorties, cessions, acquittements)
• Gérer les stocks en temps réel (volumes ambiants et à 15°C)
• Générer des rapports et états périodiques
• Recevoir des notifications sur les événements critiques du dépôt

L'application est réservée à un usage professionnel B2B dans le cadre des activités de distribution de produits pétroliers.`,
  },
  {
    title: '3. Accès et sécurité du compte',
    body: `L'accès à l'application est conditionné à la possession d'un compte utilisateur valide, créé et géré par l'administrateur de la plateforme.

L'utilisateur est seul responsable de la confidentialité de ses identifiants (nom d'utilisateur et mot de passe). Il s'engage à :

• Ne pas partager ses identifiants avec des tiers
• Informer immédiatement l'administrateur de toute utilisation non autorisée de son compte
• Se déconnecter de l'application après chaque session sur un appareil partagé
• Utiliser la fonctionnalité biométrique (Face ID / Touch ID) uniquement sur un appareil personnel et sécurisé

SANKE ne saurait être tenu responsable de tout dommage résultant d'un accès non autorisé au compte de l'utilisateur.`,
  },
  {
    title: '4. Utilisation des données',
    body: `Les données saisies dans l'application (volumes, mouvements, références) sont enregistrées sur les serveurs sécurisés de SANKE et constituent des données professionnelles sensibles.

L'utilisateur s'engage à ne saisir que des données exactes et conformes aux opérations réelles effectuées au dépôt. Toute falsification de données est strictement interdite et susceptible d'engager la responsabilité civile et pénale de l'utilisateur.

Les données de connexion et d'activité peuvent être collectées à des fins d'audit et de sécurité conformément à la politique de confidentialité de SANKE.`,
  },
  {
    title: '5. Responsabilités de l\'utilisateur',
    body: `L'utilisateur s'engage à utiliser l'application de manière conforme à sa destination et aux réglementations en vigueur dans le secteur pétrolier.

Il lui est notamment interdit de :
• Tenter de contourner les mécanismes de sécurité de l'application
• Accéder à des données auxquelles il n'est pas autorisé
• Utiliser l'application à des fins autres que la gestion professionnelle du dépôt
• Reproduire, modifier ou distribuer tout ou partie de l'application sans autorisation préalable

L'utilisateur est responsable de la conformité de ses opérations avec les lois et règlements applicables au commerce des produits pétroliers.`,
  },
  {
    title: '6. Confidentialité',
    body: `Les informations relatives aux mouvements, stocks et opérations enregistrées dans l'application sont strictement confidentielles. L'utilisateur s'engage à ne pas divulguer ces informations à des personnes non habilitées, qu'elles soient internes ou externes à son organisation.

SANKE met en œuvre les mesures techniques et organisationnelles appropriées pour protéger les données contre tout accès, modification, divulgation ou destruction non autorisés. Les tokens d'authentification sont stockés de manière sécurisée sur l'appareil de l'utilisateur (Secure Store).`,
  },
  {
    title: '7. Modification des conditions',
    body: `SANKE se réserve le droit de modifier les présentes CGU à tout moment. Les utilisateurs seront informés de toute modification significative par notification dans l'application.

La poursuite de l'utilisation de l'application après notification des modifications vaut acceptation des nouvelles conditions. En cas de désaccord avec les nouvelles conditions, l'utilisateur doit cesser d'utiliser l'application et contacter son administrateur.`,
  },
  {
    title: '8. Contact et support',
    body: `Pour toute question relative à l'utilisation de l'application, à votre compte, ou aux présentes conditions, veuillez contacter :

Support technique SANKE
Email : support@sanke.com
Horaires : Lundi – Vendredi, 08h00 – 18h00

Pour les urgences liées aux opérations de dépôt, contactez directement le responsable de votre dépôt.`,
  },
];

export function ConditionsUtilisationScreen() {
  const navigation = useNavigation();

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={20} color={Colors.ink} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Conditions d'utilisation</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        {/* Intro card */}
        <View style={styles.introCard}>
          <View style={styles.introIcon}>
            <Ionicons name="document-text" size={22} color={Colors.navy} />
          </View>
          <View style={styles.introBody}>
            <Text style={styles.introTitle}>SGDS — Application professionnelle</Text>
            <Text style={styles.introSub}>
              En utilisant cette application, vous acceptez les conditions ci-dessous.
            </Text>
          </View>
        </View>

        {/* Sections */}
        {SECTIONS.map((section, idx) => (
          <View key={idx} style={styles.section}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            <Text style={styles.sectionBody}>{section.body}</Text>
          </View>
        ))}

        {/* Footer */}
        <View style={styles.footerCard}>
          <Ionicons name="time-outline" size={14} color={Colors.slate} />
          <Text style={styles.footerText}>
            Dernière mise à jour : {LAST_UPDATE}
          </Text>
        </View>
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.paper },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.cloud,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: Colors.cloud,
    alignItems: 'center', justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 15, fontWeight: '800', color: Colors.ink, letterSpacing: -0.2,
  },

  content: { padding: 16 },

  introCard: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 12,
    backgroundColor: Colors.navyTint,
    borderRadius: Radius.lg,
    padding: 14,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: Colors.navy + '20',
  },
  introIcon: {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: Colors.white,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: Colors.navy,
    shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2,
  },
  introBody:  { flex: 1 },
  introTitle: { fontSize: 13, fontWeight: '800', color: Colors.navy, marginBottom: 4 },
  introSub:   { fontSize: 12, color: Colors.graphite, lineHeight: 18 },

  section: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.cloud,
  },
  sectionTitle: {
    fontSize: 13, fontWeight: '800', color: Colors.navy,
    marginBottom: 10, letterSpacing: -0.1,
  },
  sectionBody: {
    fontSize: 13, color: Colors.graphite, lineHeight: 20,
  },

  footerCard: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    justifyContent: 'center',
    paddingVertical: 16,
  },
  footerText: { fontSize: 12, color: Colors.slate },
});
