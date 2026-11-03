import { Pressable, Text, StyleSheet } from 'react-native';
import { useTheme } from '../theme';

export default function PrimaryButton({ title, onPress, disabled, variant = 'primary' }) {
  const theme = useTheme();
  const backgroundColor = disabled
    ? theme.border
    : variant === 'danger'
    ? theme.danger
    : variant === 'secondary'
    ? theme.surface
    : theme.primary;
  const textColor = variant === 'secondary' && !disabled ? theme.text : '#FFFFFF';

  return (
    <Pressable onPress={onPress} disabled={disabled} style={[styles.button, { backgroundColor }]}>
      <Text style={[styles.label, { color: textColor }]}>{title}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 8,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
  },
});
