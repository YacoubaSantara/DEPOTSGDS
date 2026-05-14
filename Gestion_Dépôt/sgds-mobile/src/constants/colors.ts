/**
 * SGDS Mobile — Design Tokens v2.0
 * Palette rafraîchie : bleu marine + accent orange, neutres tièdes, radius généreux.
 */
export const Colors = {
  // Brand
  navy:         '#0E2A47',
  navyDeep:     '#081A2E',
  navySoft:     '#1B3F66',
  navyTint:     '#E8EEF6',
  orange:       '#E67A2A',
  orangeSoft:   '#FFE3CC',
  orangeDeep:   '#B95A14',

  // Neutres
  ink:          '#0B1220',
  graphite:     '#3A4150',
  slate:        '#6B7589',
  silver:       '#A8B0BF',
  mist:         '#DDE2EC',
  cloud:        '#EFF2F7',
  paper:        '#F7F8FB',
  white:        '#FFFFFF',

  // Statuts
  green:        '#1F9D55',
  greenSoft:    '#D8F3E2',
  red:          '#D63B3B',
  redSoft:      '#FBE0E0',
  amber:        '#E0A21A',
  amberSoft:    '#FBEFCC',
  cyan:         '#1497B8',
  cyanSoft:     '#D2EFF6',
  purple:       '#6E47C7',
  purpleSoft:   '#E5DDF7',

  // Types de mouvements
  entree:       '#1F9D55',
  sortie:       '#D63B3B',
  cession:      '#6E47C7',
  acquittement: '#1497B8',

  // Aliases legacy (compatibilité composants existants)
  primary:      '#0E2A47',
  primaryLight: '#1B3F66',
  primaryDark:  '#081A2E',
  accent:       '#E67A2A',
  accentLight:  '#FFE3CC',
  success:      '#1F9D55',
  warning:      '#E0A21A',
  danger:       '#D63B3B',
  info:         '#1497B8',
  background:   '#F7F8FB',
  surface:      '#FFFFFF',
  border:       '#DDE2EC',
  muted:        '#6B7589',
  textPrimary:  '#0B1220',
  textSecondary:'#3A4150',
} as const;

export const Spacing = {
  xs:  4,
  sm:  8,
  md:  16,
  lg:  24,
  xl:  32,
  xxl: 48,
} as const;

export const FontSize = {
  xs:   11,
  sm:   13,
  md:   15,
  lg:   17,
  xl:   20,
  xxl:  24,
  xxxl: 30,
} as const;

export const Radius = {
  sm:  8,
  md:  14,
  lg:  20,
  xl:  28,
  pill: 999,
} as const;

export const TypeMeta: Record<string, { label: string; color: string; soft: string; glyph: string }> = {
  ENTREE:       { label: 'Entrée',       color: Colors.entree,       soft: Colors.greenSoft,  glyph: '↓' },
  SORTIE:       { label: 'Sortie',       color: Colors.sortie,       soft: Colors.redSoft,    glyph: '↑' },
  CESSION:      { label: 'Cession',      color: Colors.cession,      soft: Colors.purpleSoft, glyph: '⇄' },
  ACQUITTEMENT: { label: 'Acquittement', color: Colors.acquittement, soft: Colors.cyanSoft,   glyph: '✓' },
};
