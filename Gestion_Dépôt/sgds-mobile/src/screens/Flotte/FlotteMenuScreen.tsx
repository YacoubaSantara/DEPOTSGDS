import React, { useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { FlotteStackParams } from '../../navigation/AppNavigator';
import { useAuth } from '../../context/AuthContext';
import { Colors } from '../../constants/colors';

type Nav = NativeStackNavigationProp<FlotteStackParams>;

export function FlotteMenuScreen() {
  const navigation = useNavigation<Nav>();
  const { user, refreshPermissions } = useAuth();
  const perms = user?.permissions ?? {};

  // Rattrape les sessions restaurées depuis un cache antérieur à ce module
  // (permissions absentes) et reflète un retrait de droit fait entre-temps.
  useFocusEffect(useCallback(() => { refreshPermissions(); }, [refreshPermissions]));

  const cards = [
    {
      key:   'CamionsList' as const,
      icon:  'car-outline',
      color: Colors.navy,
      soft:  Colors.navyTint,
      title: 'Mes Camions',
      desc:  'Consultez, ajoutez ou modifiez vos camions citernes.',
      visible: perms.voir_camion,
    },
    {
      key:   'ChauffeursList' as const,
      icon:  'person-outline',
      color: Colors.orange,
      soft:  Colors.orangeSoft,
      title: 'Mes Chauffeurs',
      desc:  'Consultez, ajoutez ou modifiez vos chauffeurs.',
      visible: perms.voir_chauffeur,
    },
  ];

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <LinearGradient
        colors={[Colors.navySoft, Colors.navy, Colors.navyDeep]}
        style={styles.hero}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.heroBlob} />
        <View style={styles.heroRow}>
          <View>
            <Text style={styles.heroSub}>Logistique</Text>
            <Text style={styles.heroTitle}>Ma Flotte</Text>
          </View>
          <View style={styles.heroIcon}>
            <Ionicons name="car-sport" size={24} color={Colors.white} />
          </View>
        </View>
        <Text style={styles.heroDesc}>
          Gérez vos camions citernes et vos chauffeurs affectés à votre marketeur.
        </Text>
      </LinearGradient>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {cards.filter(c => c.visible !== false).map((c) => (
          <TouchableOpacity
            key={c.key}
            style={styles.card}
            onPress={() => navigation.navigate(c.key)}
            activeOpacity={0.75}
          >
            <View style={[styles.cardIcon, { backgroundColor: c.soft }]}>
              <Ionicons name={c.icon as any} size={28} color={c.color} />
            </View>
            <View style={styles.cardBody}>
              <Text style={styles.cardTitle}>{c.title}</Text>
              <Text style={styles.cardDesc}>{c.desc}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={Colors.silver} />
          </TouchableOpacity>
        ))}

        {cards.every(c => c.visible === false) && (
          <View style={styles.empty}>
            <Ionicons name="lock-closed-outline" size={32} color={Colors.silver} />
            <Text style={styles.emptyText}>Aucun accès à la flotte pour votre compte.</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:  { flex: 1, backgroundColor: Colors.paper },
  scroll: { flex: 1 },
  content: { padding: 16, paddingBottom: 40 },

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
  cardTitle: { fontSize: 15, fontWeight: '800', color: Colors.ink, marginBottom: 4 },
  cardDesc: { fontSize: 11, color: Colors.slate, lineHeight: 16 },

  empty: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyText: { fontSize: 13, color: Colors.slate, textAlign: 'center' },
});
