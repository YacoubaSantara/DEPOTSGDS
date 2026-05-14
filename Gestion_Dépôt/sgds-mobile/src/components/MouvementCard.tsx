import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Radius, TypeMeta } from '../constants/colors';
import { MouvementListItem } from '../api/mouvements';

interface Props {
  mouvement: MouvementListItem;
  onPress: () => void;
}

function fmtN(n: any): string {
  const v = Number(n);
  if (isNaN(v)) return '0';
  return v.toLocaleString('fr-FR', { maximumFractionDigits: 0 });
}

export function MouvementCard({ mouvement, onPress }: Props) {
  const meta  = TypeMeta[mouvement.type] ?? {
    label: mouvement.type, color: Colors.slate, soft: Colors.cloud, glyph: '·',
  };
  const date  = new Date(mouvement.date ?? '');
  const time  = isNaN(date.getTime())
    ? ''
    : date.getHours().toString().padStart(2, '0') + ':' + date.getMinutes().toString().padStart(2, '0');

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      {/* Glyph badge */}
      <View style={[styles.glyph, { backgroundColor: meta.soft }]}>
        <Text style={[styles.glyphText, { color: meta.color }]}>{meta.glyph}</Text>
      </View>

      <View style={styles.body}>
        {/* Ligne 1: type + heure */}
        <View style={styles.row1}>
          <Text style={[styles.typeText, { color: meta.color }]}>{meta.label}</Text>
          <View style={styles.dot} />
          <Text style={styles.timeText}>{time}</Text>
        </View>
        {/* Ligne 2: sigle + produit */}
        <Text style={styles.produit} numberOfLines={1}>
          {mouvement.produit_sigle ? `[${mouvement.produit_sigle}] ` : ''}
          {mouvement.produit}
        </Text>
        {/* Destination */}
        {(mouvement as any).destination && (
          <Text style={styles.dest} numberOfLines={1}>
            <Ionicons name="location-outline" size={10} color={Colors.silver} />
            {' '}{(mouvement as any).destination}
          </Text>
        )}
      </View>

      {/* Quantité */}
      <View style={styles.qteBlock}>
        <Text style={[styles.qteValue, { color: meta.color }]}>
          {mouvement.type === 'ENTREE' ? '+' : mouvement.type === 'SORTIE' ? '−' : '·'}{' '}
          {fmtN((mouvement as any).quantite_ambiant)}
        </Text>
        <Text style={styles.qteUnit}>L</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    padding: 12,
    backgroundColor: Colors.white,
    borderWidth: 1, borderColor: Colors.cloud,
    borderRadius: Radius.md,
    shadowColor: Colors.ink,
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 2, elevation: 1,
  },
  glyph: {
    width: 38, height: 38, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
  },
  glyphText:  { fontSize: 18, fontWeight: '800', lineHeight: 22 },
  body:       { flex: 1, minWidth: 0 },
  row1:       { flexDirection: 'row', alignItems: 'center', gap: 6 },
  typeText:   { fontSize: 10, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.5 },
  dot:        { width: 3, height: 3, borderRadius: 1.5, backgroundColor: Colors.silver },
  timeText:   { fontSize: 10, color: Colors.slate },
  produit:    { fontSize: 13, fontWeight: '600', color: Colors.ink, marginTop: 2 },
  dest:       { fontSize: 10, color: Colors.slate, marginTop: 1 },
  qteBlock:   { alignItems: 'flex-end' },
  qteValue:   { fontSize: 13, fontWeight: '800' },
  qteUnit:    { fontSize: 9, color: Colors.slate, marginTop: 1 },
});
