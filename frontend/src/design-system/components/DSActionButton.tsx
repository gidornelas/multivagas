import { Button, type ButtonProps } from 'antd'
import type { CSSProperties } from 'react'

type DSActionButtonProps = ButtonProps & {
  emphasis?: 'primary' | 'soft' | 'ghost'
}

const baseStyle = {
  height: 42,
  borderRadius: '999px',
  paddingInline: 18,
  fontWeight: 700,
  letterSpacing: '-0.01em',
} satisfies CSSProperties

export function DSActionButton({
  emphasis = 'primary',
  style,
  children,
  ...props
}: DSActionButtonProps) {
  if (emphasis === 'ghost') {
    return (
      <Button
        {...props}
        style={{
          ...baseStyle,
          borderColor: 'var(--ds-color-border)',
          background: 'rgba(255,255,255,0.56)',
          color: 'var(--ds-color-text)',
          boxShadow: 'none',
          ...style,
        }}
      >
        {children}
      </Button>
    )
  }

  if (emphasis === 'soft') {
    return (
      <Button
        {...props}
        style={{
          ...baseStyle,
          borderColor: 'var(--ds-color-primary-border)',
          background:
            'linear-gradient(180deg, var(--ds-color-primary-bg), rgba(255,255,255,0.85))',
          color: 'var(--ds-color-primary)',
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.7)',
          ...style,
        }}
      >
        {children}
      </Button>
    )
  }

  return (
    <Button
      type="primary"
      {...props}
      style={{
        ...baseStyle,
        borderColor: 'transparent',
        background:
          'linear-gradient(135deg, var(--ds-color-primary), var(--ds-color-primary-hover))',
        color: 'var(--ds-color-on-primary)',
        boxShadow: 'var(--ds-shadow-1)',
        ...style,
      }}
    >
      {children}
    </Button>
  )
}
