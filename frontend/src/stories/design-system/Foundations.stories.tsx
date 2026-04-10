import type { Meta, StoryObj } from '@storybook/react-vite'
import { Card, Col, Row, Space, Typography } from 'antd'

import { dashboardTokens } from '../../design-system/tokens'

type Swatch = {
  name: string
  value: string
}

const swatches: Swatch[] = [
  { name: 'Primary', value: dashboardTokens.colorPrimary },
  { name: 'Primary Bg', value: dashboardTokens.colorPrimaryBg },
  { name: 'Success', value: dashboardTokens.colorSuccess },
  { name: 'Success Bg', value: dashboardTokens.colorSuccessBg },
  { name: 'Warning', value: dashboardTokens.colorWarning },
  { name: 'Warning Bg', value: dashboardTokens.colorWarningBg },
  { name: 'Error', value: dashboardTokens.colorError },
  { name: 'Error Bg', value: dashboardTokens.colorErrorBg },
  { name: 'Info', value: dashboardTokens.colorInfo },
  { name: 'Info Bg', value: dashboardTokens.colorInfoBg },
  { name: 'Surface', value: dashboardTokens.colorBgContainer },
  { name: 'Layout', value: dashboardTokens.colorBgLayout },
]

function FoundationsPreview() {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 1100 }}>
      <Card title="Cores semânticas">
        <Row gutter={[12, 12]}>
          {swatches.map((item) => (
            <Col key={item.name} xs={24} sm={12} md={8} lg={6}>
              <div
                style={{
                  border: '1px solid var(--ds-color-border)',
                  borderRadius: 'var(--ds-radius-sm)',
                  overflow: 'hidden',
                }}
              >
                <div style={{ background: item.value, height: 64 }} />
                <div style={{ padding: 10 }}>
                  <Typography.Text strong>{item.name}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {item.value}
                  </Typography.Text>
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      <Card title="Escala de tipografia">
        <Space direction="vertical" size={4}>
          <Typography.Title level={1} style={{ margin: 0 }}>
            Dashboard H1
          </Typography.Title>
          <Typography.Title level={3} style={{ margin: 0 }}>
            Dashboard H3
          </Typography.Title>
          <Typography.Text>
            Texto base para tabelas, cards e descrição de vagas.
          </Typography.Text>
          <Typography.Text type="secondary">Texto secundário para contexto e metadata.</Typography.Text>
        </Space>
      </Card>

      <Card title="Raio, sombra e spacing">
        <Space size="large" wrap>
          <div
            style={{
              width: 200,
              height: 90,
              borderRadius: dashboardTokens.borderRadius,
              boxShadow: dashboardTokens.boxShadow,
              border: '1px solid var(--ds-color-border)',
              background: '#fff',
              padding: dashboardTokens.paddingSM,
            }}
          >
            <Typography.Text strong>Card padrão</Typography.Text>
          </div>
          <div
            style={{
              width: 200,
              height: 90,
              borderRadius: dashboardTokens.borderRadiusLG,
              boxShadow: dashboardTokens.boxShadowSecondary,
              border: '1px solid var(--ds-color-border)',
              background: '#fff',
              padding: dashboardTokens.padding,
            }}
          >
            <Typography.Text strong>Card elevado</Typography.Text>
          </div>
        </Space>
      </Card>
    </Space>
  )
}

const meta = {
  title: 'Design System/Foundations',
  component: FoundationsPreview,
  parameters: {
    layout: 'padded',
  },
} satisfies Meta<typeof FoundationsPreview>

export default meta

type Story = StoryObj<typeof meta>

export const Overview: Story = {}
