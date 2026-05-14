import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, FontSize, Spacing, Radius } from '../constants/colors';

interface Props {
  titre: string;
  sigle: string;
  stockAmbiant: number;
  stock15: number;
}

function fmt(n: number | null | undefined): string {
  if (n == null || isNaN(Number(n))) return '0';
  return Number(n).toLocaleString('fr-FR', { maximumFractionDigits: 3 });
}

export function KpiCard({ titre, sigle, stockAmbiant, stock15 }: Props) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{sigle}</Text>
        </View>
        <Text style={styles.titre} numberOfLines={2}>{titre}</Text>
      </View>

      <View style={styles.row}>
        <View style={styles.col}>
          <Text style={styles.label}>Ambiant</Text>
          <Text style={styles.value}>{fmt(stockAmbiant)}</Text>
          <Text style={styles.unit}>L</Text>
        </View>
        <View style={styles.divider} />
        <View style={styles.col}>
          <Text style={styles.label}>15°C</Text>
          <Text style={styles.value}>{fmt(stock15)}</Text>
          <Text style={styles.unit}>L</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    marginHorizontal: Spacing.md,
    marginBottom: Spacing.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  badge: {
    backgroundColor: Colors.primary,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    marginRight: Spacing.sm,
  },
  badgeText: {
    color: Colors.white,
    fontWeight: '700',
    fontSize: FontSize.sm,
  },
  titre: {
    flex: 1,
    fontSize: FontSize.md,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  col: {
    flex: 1,
    alignItems: 'center',
  },
  divider: {
    width: 1,
    height: 40,
    backgroundColor: Colors.border,
  },
  label: {
    fontSize: FontSize.xs,
    color: Colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  value: {
    fontSize: FontSize.xl,
    fontWeight: '700',
    color: Colors.primary,
    marginTop: 2,
  },
  unit: {
    fontSize: FontSize.xs,
    color: Colors.muted,
  },
});
