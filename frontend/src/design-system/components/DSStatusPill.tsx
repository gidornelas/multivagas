import { Tag } from 'antd'

import { statusTokens, type DashboardStatus } from '../tokens'

type DSStatusPillProps = {
  status: DashboardStatus
  label?: string
}

export function DSStatusPill({ status, label }: DSStatusPillProps) {
  const tone = statusTokens[status]

  return (
    <Tag
      style={{
        marginInlineEnd: 0,
        borderRadius: 999,
        borderColor: tone.border,
        background: tone.bg,
        color: tone.text,
        fontWeight: 700,
        fontSize: 11,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        paddingInline: 12,
        paddingBlock: 6,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.72)',
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: tone.dot,
          boxShadow: `0 0 0 4px color-mix(in srgb, ${tone.dot} 14%, transparent)`,
        }}
      />
      {label ?? status}
    </Tag>
  )
}
