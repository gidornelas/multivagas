import type { Meta, StoryObj } from '@storybook/react-vite'
import { CalendarOutlined } from '@ant-design/icons'
import { Card, Col, Flex, Row, Space, Typography } from 'antd'

import { DSActionButton } from '../../design-system/components/DSActionButton'
import { DSStatCard } from '../../design-system/components/DSStatCard'
import { DSStatusPill } from '../../design-system/components/DSStatusPill'

function DashboardComposition() {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} lg={6}>
          <DSStatCard label="Vagas coletadas" value={467} helper="última rodada" tone="primary" />
        </Col>
        <Col xs={24} md={12} lg={6}>
          <DSStatCard label="Pipeline" value={67} helper="score >= 80" percent={74} tone="info" />
        </Col>
        <Col xs={24} md={12} lg={6}>
          <DSStatCard label="Aplicadas" value={22} helper="últimos 30 dias" percent={88} tone="success" />
        </Col>
        <Col xs={24} md={12} lg={6}>
          <DSStatCard label="Recusadas" value={4} helper="tracking" percent={12} tone="error" />
        </Col>
      </Row>

      <Card
        title="UI/UX Designer — Talentflix"
        style={{ borderRadius: 'var(--ds-radius)', borderColor: 'var(--ds-color-border)' }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Flex justify="space-between" align="center" wrap>
            <Typography.Text type="secondary">Remoto • Brasil</Typography.Text>
            <DSStatusPill status="processo" label="em processo" />
          </Flex>

          <Flex justify="space-between" align="center" wrap>
            <Space>
              <CalendarOutlined />
              <Typography.Text type="secondary">Aplicada em 09/04/2026</Typography.Text>
            </Space>
            <Typography.Text strong>Follow-up 16/04/2026</Typography.Text>
          </Flex>

          <Flex justify="end" gap={8} wrap>
            <DSActionButton emphasis="soft">Ver vaga</DSActionButton>
            <DSActionButton emphasis="primary">Preparar follow-up</DSActionButton>
          </Flex>
        </Space>
      </Card>
    </Space>
  )
}

const meta = {
  title: 'Design System/Templates/Dashboard Composition',
  component: DashboardComposition,
  parameters: {
    layout: 'padded',
  },
} satisfies Meta<typeof DashboardComposition>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
