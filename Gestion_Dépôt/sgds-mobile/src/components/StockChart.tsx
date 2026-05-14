/**
 * Graphique stock — barres horizontales par produit
 * Implémentation native sans librairie externe
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Spacing, Radius, FontSize } from '../constants/colors';
import { StockProduit } from '../api/dashboard';

interface Props {
  stocks: StockProduit[];
}

const BAR_COLORS = [
  '#1a3a5c', '#2d5a8e', '#e07b2a', '#28a745',
  '#6f42c1', '#17a2b8', '#dc3545', '#fd7e14',
];

function fmt(n: any): string {
  const v = Number(n);
  if (isNaN(v)) return '0';
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M';
  if (v >= 1_000)     return (v / 1_000).toFixed(0) + 'k';
  return v.toFixed(0);
}

export function StockChart({ stocks }: Props) {
  if (!stocks || stocks.length === 0) return null;

  const maxVal = Math.max(...stocks.map(s => Math.max(Number(s.stock_ambiant) || 0, 0.1)));

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Niveaux de stock (Ambiant)</Text>

      {stocks.map((stock, idx) => {
        const val     = Math.max(Number(stock.stock_ambiant) || 0, 0);
        const val15   = Math.max(Number(stock.stock_15) || 0, 0);
        const pct     = Math.min((val / maxVal) * 100, 100);
        const pct15   = Math.min((val15 / maxVal) * 100, 100);
        const color   = BAR_COLORS[idx % BAR_COLORS.length];

        return (
          <View key={stock.produit_id} style={styles.barRow}>
            {/* Étiquette produit */}
            <View style={styles.labelCol}>
              <Text style={styles.sigle} numberOfLines={1}>{stock.produit_sigle}</Text>
            </View>

            {/* Barres */}
            <View style={styles.barsCol}>
              {/* Ambiant */}
              <View style={styles.barTrack}>
                <View style={[styles.bar, { width: `${pct}%`, backgroundColor: color }]} />
                <Text style={styles.barVal}>{fmt(val)} L</Text>
              </View>
              {/* 15°C */}
              <View style={[styles.barTrack, { marginTop: 2 }]}>
                <View style={[styles.bar, { width: `${pct15}%`, backgroundColor: color + '70' }]} />
                <Text style={[styles.barVal, { color: Colors.muted }]}>{fmt(val15)} L</Text>
              </View>
            </View>
          </View>
        );
      })}

      {/* Légende */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: Colors.primary }]} />
          <Text style={styles.legendText}>Ambiant</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: Colors.primary + '70' }]} />
          <Text style={styles.legendText}>15°C</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.white,
    marginHorizontal: Spacing.md,
    marginBottom: Spacing.sm,
    borderRadius: Radius.md,
    padding: Spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  title: {
    fontSize: FontSize.sm,
    fontWeight: '700',
    color: Colors.primary,
    marginBottom: Spacing.sm,
  },
  barRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  labelCol: {
    width: 44,
    marginRight: 8,
  },
  sigle: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSecondary,
    textAlign: 'right',
  },
  barsCol: {
    flex: 1,
  },
  barTrack: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 14,
    backgroundColor: Colors.background,
    borderRadius: 7,
    overflow: 'hidden',
  },
  bar: {
    height: '100%',
    borderRadius: 7,
    minWidth: 4,
  },
  barVal: {
    position: 'absolute',
    right: 4,
    fontSize: 9,
    fontWeight: '600',
    color: Colors.white,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: Spacing.sm,
    gap: 12,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 10,
    color: Colors.muted,
  },
});
