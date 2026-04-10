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
        fontWeight: 600,
        paddingInline: 10,
      }}
    >
      {label ?? status}
    </Tag>
  )
}
