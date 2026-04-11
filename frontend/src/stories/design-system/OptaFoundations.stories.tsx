import type { Meta, StoryObj } from '@storybook/react-vite'
import { Card, Col, Flex, Row, Space, Typography } from 'antd'

import { DSActionButton } from '../../design-system/components/DSActionButton'
import { DSStatusPill } from '../../design-system/components/DSStatusPill'
import { dashboardTokens } from '../../design-system/tokens'

type Swatch = {
  name: string
  value: string
}

const brandSwatches: Swatch[] = [
  { name: 'Signal Orange', value: dashboardTokens.colorPrimary },
  { name: 'Decision Glow', value: dashboardTokens.colorPrimaryBg },
  { name: 'Intelligence Teal', value: dashboardTokens.colorSuccess },
  { name: 'System Teal Wash', value: dashboardTokens.colorSuccessBg },
  { name: 'Signal Blue', value: dashboardTokens.colorInfo },
  { name: 'Porcelain', value: dashboardTokens.colorBgContainer },
  { name: 'Canvas Sand', value: dashboardTokens.colorBgBase },
  { name: 'Ink Dark', value: dashboardTokens.colorBgCanvasDark },
]

function OptaFoundationsPreview() {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 1180 }}>
      <Card
        style={{
          borderRadius: 'var(--ds-radius-lg)',
          borderColor: 'var(--ds-color-border)',
          boxShadow: 'var(--ds-shadow-2)',
          background:
            'linear-gradient(135deg, rgba(255,255,255,0.96), color-mix(in srgb, var(--ds-color-primary-bg) 36%, white))',
        }}
        bodyStyle={{ padding: 'var(--ds-space-lg)' }}
      >
        <Row gutter={[28, 28]} align="middle">
          <Col xs={24} lg={14}>
            <Space direction="vertical" size={14}>
              <Typography.Text
                style={{
                  textTransform: 'uppercase',
                  letterSpacing: '0.14em',
                  color: 'var(--ds-color-primary)',
                  fontWeight: 800,
                }}
              >
                Opta Design System
              </Typography.Text>
              <Typography.Title
                level={1}
                className="ds-display"
                style={{ margin: 0, fontSize: 44, lineHeight: 1.04, maxWidth: 680 }}
              >
                Uma linguagem de decisao, fluxo e clareza operacional.
              </Typography.Title>
              <Typography.Paragraph
                style={{
                  margin: 0,
                  fontSize: 16,
                  color: 'var(--ds-color-text-secondary)',
                  maxWidth: 600,
                }}
              >
                O sistema abandona a neutralidade generica e assume uma combinacao de calor
                editorial, densidade tecnologica e hierarquia de produto.
              </Typography.Paragraph>
            </Space>
          </Col>
          <Col xs={24} lg={10}>
            <Card
              style={{
                borderRadius: 'var(--ds-radius-lg)',
                background: 'var(--ds-color-bg-dark)',
                borderColor: 'rgba(255,255,255,0.06)',
                color: '#fff',
              }}
              bodyStyle={{ padding: 'var(--ds-space)' }}
            >
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <Typography.Text style={{ color: 'rgba(255,255,255,0.66)', fontWeight: 700 }}>
                  Opta principles
                </Typography.Text>
                <Flex gap={10} wrap>
                  <DSStatusPill status="aplicada" label="decisao" />
                  <DSStatusPill status="entrevista" label="progresso" />
                  <DSStatusPill status="processo" label="sinal" />
                </Flex>
                <Flex gap={10} wrap>
                  <DSActionButton emphasis="primary">Acao principal</DSActionButton>
                  <DSActionButton emphasis="soft">Acao contextual</DSActionButton>
                </Flex>
              </Space>
            </Card>
          </Col>
        </Row>
      </Card>

      <Card title="Paleta de marca" style={{ borderRadius: 'var(--ds-radius)' }}>
        <Row gutter={[14, 14]}>
          {brandSwatches.map((item) => (
            <Col key={item.name} xs={24} sm={12} md={8} lg={6}>
              <div
                style={{
                  border: '1px solid var(--ds-color-border)',
                  borderRadius: 'var(--ds-radius-sm)',
                  overflow: 'hidden',
                  background: 'var(--ds-color-bg-container)',
                }}
              >
                <div style={{ background: item.value, height: 72 }} />
                <div style={{ padding: 14 }}>
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

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Tipografia" style={{ borderRadius: 'var(--ds-radius)' }}>
            <Space direction="vertical" size={8}>
              <Typography.Title
                level={1}
                className="ds-display"
                style={{ margin: 0, fontSize: 40, lineHeight: 1.02 }}
              >
                Prioridade visual em uma camada.
              </Typography.Title>
              <Typography.Title level={4} style={{ margin: 0 }}>
                Titulos com mais intencao e menos ruido.
              </Typography.Title>
              <Typography.Text>
                A base textual foi desenhada para leitura longa, dados operacionais e modulos
                de produto com alto volume de informacao.
              </Typography.Text>
              <Typography.Text type="secondary">
                Metadados e contexto usam contraste mais suave para manter respiro sem perder
                densidade.
              </Typography.Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Superficies e profundidade" style={{ borderRadius: 'var(--ds-radius)' }}>
            <Flex gap={16} wrap>
              <div
                style={{
                  width: 220,
                  minHeight: 112,
                  borderRadius: 'var(--ds-radius)',
                  boxShadow: 'var(--ds-shadow-1)',
                  border: '1px solid var(--ds-color-border)',
                  background: 'var(--ds-color-bg-container)',
                  padding: 'var(--ds-space-sm)',
                }}
              >
                <Typography.Text strong>Card operacional</Typography.Text>
                <br />
                <Typography.Text type="secondary">Claro, poroso e legivel.</Typography.Text>
              </div>
              <div
                style={{
                  width: 220,
                  minHeight: 112,
                  borderRadius: 'var(--ds-radius-lg)',
                  boxShadow: 'var(--ds-shadow-2)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  background: 'var(--ds-color-bg-dark-alt)',
                  color: '#fff',
                  padding: 'var(--ds-space-sm)',
                }}
              >
                <Typography.Text strong style={{ color: '#fff' }}>
                  Painel de decisao
                </Typography.Text>
                <br />
                <Typography.Text style={{ color: 'rgba(255,255,255,0.68)' }}>
                  Escuro, denso e tecnologico.
                </Typography.Text>
              </div>
            </Flex>
          </Card>
        </Col>
      </Row>
    </Space>
  )
}

const meta = {
  title: 'Opta Design System/Foundations',
  component: OptaFoundationsPreview,
  parameters: {
    layout: 'padded',
  },
} satisfies Meta<typeof OptaFoundationsPreview>

export default meta

type Story = StoryObj<typeof meta>

export const Overview: Story = {}
