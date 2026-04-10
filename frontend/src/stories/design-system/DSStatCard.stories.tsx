import type { Meta, StoryObj } from '@storybook/react-vite'
import { Col, Row } from 'antd'

import { DSStatCard } from '../../design-system/components/DSStatCard'

const meta = {
  title: 'Design System/Components/Stat Card',
  component: DSStatCard,
  parameters: {
    layout: 'padded',
  },
  args: {
    label: 'Pipeline (>= 80)',
    value: 67,
    helper: 'Prontas para candidatura',
    percent: 74,
    tone: 'primary',
  },
} satisfies Meta<typeof DSStatCard>

export default meta

type Story = StoryObj<typeof meta>

export const Primary: Story = {}

export const Success: Story = {
  args: {
    label: 'Candidaturas enviadas',
    value: 22,
    helper: 'Últimos 30 dias',
    percent: 88,
    tone: 'success',
  },
}

export const DashboardGrid: Story = {
  render: () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} md={12} lg={6}>
        <DSStatCard label="Vagas coletadas" value={467} helper="Última rodada" tone="primary" />
      </Col>
      <Col xs={24} md={12} lg={6}>
        <DSStatCard label="Pipeline" value={67} helper="Score >= 80" percent={74} tone="info" />
      </Col>
      <Col xs={24} md={12} lg={6}>
        <DSStatCard label="Entrevistas" value={9} helper="Em andamento" percent={32} tone="success" />
      </Col>
      <Col xs={24} md={12} lg={6}>
        <DSStatCard label="Recusadas" value={4} helper="Últimos 14 dias" percent={12} tone="error" />
      </Col>
    </Row>
  ),
}
