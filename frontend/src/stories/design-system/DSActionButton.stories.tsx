import type { Meta, StoryObj } from '@storybook/react-vite'
import { Space } from 'antd'

import { DSActionButton } from '../../design-system/components/DSActionButton'

const meta = {
  title: 'Design System/Components/Action Button',
  component: DSActionButton,
  parameters: {
    layout: 'centered',
  },
  args: {
    children: 'Salvar configurações',
  },
} satisfies Meta<typeof DSActionButton>

export default meta

type Story = StoryObj<typeof meta>

export const Primary: Story = {
  args: {
    emphasis: 'primary',
  },
}

export const Soft: Story = {
  args: {
    emphasis: 'soft',
    children: 'Visualizar detalhes',
  },
}

export const Pair: Story = {
  render: () => (
    <Space>
      <DSActionButton emphasis="soft">Cancelar</DSActionButton>
      <DSActionButton emphasis="primary">Aplicar tokens</DSActionButton>
    </Space>
  ),
}
