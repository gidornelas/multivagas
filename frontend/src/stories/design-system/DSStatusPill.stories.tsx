import type { Meta, StoryObj } from '@storybook/react-vite'
import { Space } from 'antd'

import { DSStatusPill } from '../../design-system/components/DSStatusPill'

const meta = {
  title: 'Design System/Components/Status Pill',
  component: DSStatusPill,
  parameters: {
    layout: 'centered',
  },
  args: {
    status: 'aplicada',
  },
} satisfies Meta<typeof DSStatusPill>

export default meta

type Story = StoryObj<typeof meta>

export const Aplicada: Story = {}

export const Entrevista: Story = {
  args: {
    status: 'entrevista',
  },
}

export const Processo: Story = {
  args: {
    status: 'processo',
  },
}

export const Recusada: Story = {
  args: {
    status: 'recusada',
  },
}

export const All: Story = {
  render: () => (
    <Space wrap>
      <DSStatusPill status="aplicada" />
      <DSStatusPill status="entrevista" />
      <DSStatusPill status="processo" />
      <DSStatusPill status="recusada" />
    </Space>
  ),
}
