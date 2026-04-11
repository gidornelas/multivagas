import { Card, Space, Typography } from 'antd'

type DSStatCardProps = {
  label: string
  value: number
  helper: string
  percent?: number
  caption?: string
  tone?: 'primary' | 'info' | 'success' | 'warning' | 'error'
}

const toneColorMap = {
  primary: 'var(--ds-color-primary)',
  info: 'var(--ds-color-info)',
  success: 'var(--ds-color-success)',
  warning: 'var(--ds-color-warning)',
  error: 'var(--ds-color-error)',
} as const

export function DSStatCard({
  label,
  value,
  helper,
  percent,
  caption,
  tone = 'primary',
}: DSStatCardProps) {
  const color = toneColorMap[tone]

  return (
    <Card
      style={{
        borderRadius: 'var(--ds-radius)',
        borderColor: 'var(--ds-color-border)',
        boxShadow: 'var(--ds-shadow-1)',
        background:
          'linear-gradient(180deg, rgba(255,255,255,0.98), color-mix(in srgb, var(--ds-color-primary-bg) 35%, #ffffff 65%))',
        overflow: 'hidden',
      }}
      bodyStyle={{ padding: 'var(--ds-space)', position: 'relative' }}
    >
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: '0 auto 0 0',
          width: 5,
          background: color,
        }}
      />

      <Space direction="vertical" size={10} style={{ width: '100%' }}>
        <Typography.Text
          type="secondary"
          style={{
            textTransform: 'uppercase',
            fontSize: 11,
            letterSpacing: '0.1em',
            fontWeight: 700,
          }}
        >
          {label}
        </Typography.Text>

        <Typography.Title
          level={2}
          style={{
            margin: 0,
            color: 'var(--ds-color-text)',
            fontFamily: 'var(--ds-font-display)',
            fontSize: 36,
            lineHeight: 1,
            letterSpacing: '-0.05em',
          }}
        >
          {value}
        </Typography.Title>

        <Typography.Text style={{ color, fontWeight: 700 }}>{helper}</Typography.Text>

        {typeof percent === 'number' ? (
          <div style={{ display: 'grid', gap: 8 }}>
            <div
              style={{
                height: 8,
                borderRadius: 999,
                background: 'var(--ds-color-border-soft)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${Math.max(0, Math.min(100, percent))}%`,
                  height: '100%',
                  borderRadius: 999,
                  background: `linear-gradient(90deg, ${color}, color-mix(in srgb, ${color} 74%, white))`,
                }}
              />
            </div>
            <Typography.Text style={{ color: 'var(--ds-color-text-secondary)', fontSize: 12 }}>
              {percent}% de conclusão
            </Typography.Text>
          </div>
        ) : null}

        {caption ? (
          <Typography.Text style={{ color: 'var(--ds-color-text-tertiary)', fontSize: 12 }}>
            {caption}
          </Typography.Text>
        ) : null}
      </Space>
    </Card>
  )
}
