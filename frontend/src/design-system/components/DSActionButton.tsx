import { Button, type ButtonProps } from 'antd'

type DSActionButtonProps = ButtonProps & {
  emphasis?: 'primary' | 'soft'
}

export function DSActionButton({ emphasis = 'primary', style, ...props }: DSActionButtonProps) {
  if (emphasis === 'soft') {
    return (
      <Button
        {...props}
        style={{
          borderRadius: 'var(--ds-radius-sm)',
          borderColor: 'var(--ds-color-info-border)',
          background: 'var(--ds-color-info-bg)',
          color: 'var(--ds-color-info)',
          ...style,
        }}
      />
    )
  }

  return <Button type="primary" {...props} style={{ borderRadius: 'var(--ds-radius-sm)', ...style }} />
}
