import { Card, Progress, Space, Typography } from 'antd'

type DSStatCardProps = {
  label: string
  value: number
  helper: string
  percent?: number
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
  tone = 'primary',
}: DSStatCardProps) {
  const color = toneColorMap[tone]

  return (
    <Card
      style={{
        borderRadius: 'var(--ds-radius)',
        borderColor: 'var(--ds-color-border)',
        boxShadow: 'var(--ds-shadow-1)',
      }}
      bodyStyle={{ padding: 'var(--ds-space)' }}
    >
      <Space direction="vertical" size={8} style={{ width: '100%' }}>
        <Typography.Text type="secondary" style={{ textTransform: 'uppercase', fontSize: 12 }}>
          {label}
        </Typography.Text>
        <Typography.Title level={2} style={{ margin: 0, color }}>
          {value}
        </Typography.Title>
        <Typography.Text type="secondary">{helper}</Typography.Text>
        {typeof percent === 'number' ? (
          <Progress
            percent={percent}
            showInfo={false}
            strokeColor={color}
            trailColor="var(--ds-color-bg-layout)"
          />
        ) : null}
      </Space>
    </Card>
  )
}
