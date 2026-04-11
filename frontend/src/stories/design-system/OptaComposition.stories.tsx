import type { Meta, StoryObj } from '@storybook/react-vite'
import { CalendarOutlined, RadarChartOutlined } from '@ant-design/icons'
import { Card, Col, Flex, Row, Space, Typography } from 'antd'

import { DSActionButton } from '../../design-system/components/DSActionButton'
import { DSStatCard } from '../../design-system/components/DSStatCard'
import { DSStatusPill } from '../../design-system/components/DSStatusPill'

function OptaCompositionPreview() {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        style={{
          borderRadius: 'var(--ds-radius-lg)',
          borderColor: 'rgba(255,255,255,0.06)',
          background:
            'linear-gradient(135deg, var(--ds-color-bg-dark), var(--ds-color-bg-dark-alt))',
          color: '#fff',
          overflow: 'hidden',
        }}
        bodyStyle={{ padding: 'var(--ds-space-lg)' }}
      >
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} lg={15}>
            <Space direction="vertical" size={14}>
              <Typography.Text
                style={{
                  color: 'rgba(255,255,255,0.62)',
                  letterSpacing: '0.14em',
                  textTransform: 'uppercase',
                  fontWeight: 700,
                }}
              >
                Opta orchestration layer
              </Typography.Text>
              <Typography.Title
                level={1}
                className="ds-display"
                style={{ color: '#fff', margin: 0, fontSize: 42, lineHeight: 1.04 }}
              >
                O design system para produto, decisao e cadencia operacional.
              </Typography.Title>
              <Typography.Paragraph
                style={{
                  color: 'rgba(255,255,255,0.72)',
                  margin: 0,
                  fontSize: 16,
                  maxWidth: 620,
                }}
              >
                A composicao mistura uma cabine escura de decisao com modulos claros de leitura,
                criando contraste entre estrategia e execucao.
              </Typography.Paragraph>
              <Flex gap={10} wrap>
                <DSActionButton emphasis="primary">Priorizar pipeline</DSActionButton>
                <DSActionButton emphasis="soft">Abrir criterios</DSActionButton>
                <DSActionButton emphasis="ghost">Ver historico</DSActionButton>
              </Flex>
            </Space>
          </Col>

          <Col xs={24} lg={9}>
            <Card
              style={{
                borderRadius: 'var(--ds-radius)',
                background: 'rgba(255,255,255,0.06)',
                borderColor: 'rgba(255,255,255,0.08)',
                backdropFilter: 'blur(10px)',
              }}
              bodyStyle={{ padding: 'var(--ds-space)' }}
            >
              <Space direction="vertical" size={14} style={{ width: '100%' }}>
                <Flex justify="space-between" align="center">
                  <Typography.Text style={{ color: '#fff', fontWeight: 700 }}>
                    Signal card
                  </Typography.Text>
                  <DSStatusPill status="entrevista" label="saudavel" />
                </Flex>
                <Typography.Title
                  level={2}
                  className="ds-display"
                  style={{ color: '#fff', margin: 0 }}
                >
                  82
                </Typography.Title>
                <Typography.Text style={{ color: 'rgba(255,255,255,0.68)' }}>
                  Score medio das vagas priorizadas nesta rodada.
                </Typography.Text>
              </Space>
            </Card>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}>
          <DSStatCard
            label="Vagas qualificadas"
            value={128}
            helper="24 novas em 7 dias"
            percent={71}
            tone="primary"
            caption="Radar de aderencia ao curriculo"
          />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <DSStatCard
            label="Sinais fortes"
            value={39}
            helper="Score acima de 80"
            percent={64}
            tone="success"
            caption="Prontas para acao de candidatura"
          />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <DSStatCard
            label="Em processo"
            value={14}
            helper="Conversas abertas"
            percent={42}
            tone="info"
            caption="Entrevistas e follow-ups ativos"
          />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <DSStatCard
            label="Risco de atraso"
            value={7}
            helper="Acoes pendentes"
            percent={22}
            tone="warning"
            caption="Itens sem proximo passo definido"
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={15}>
          <Card style={{ borderRadius: 'var(--ds-radius)', boxShadow: 'var(--ds-shadow-1)' }}>
            <Space direction="vertical" size={18} style={{ width: '100%' }}>
              <Flex justify="space-between" align="start" wrap gap={12}>
                <div>
                  <Typography.Title level={3} className="ds-display" style={{ margin: 0 }}>
                    Senior Product Designer - TalentOS
                  </Typography.Title>
                  <Typography.Text type="secondary">
                    Plataforma B2B de recrutamento • Remoto • Brasil
                  </Typography.Text>
                </div>
                <DSStatusPill status="aplicada" label="prioridade alta" />
              </Flex>

              <Flex gap={10} wrap>
                <DSStatusPill status="processo" label="follow-up amanha" />
                <DSStatusPill status="entrevista" label="boa aderencia" />
              </Flex>

              <Row gutter={[12, 12]}>
                <Col xs={24} md={12}>
                  <Card
                    size="small"
                    style={{
                      borderRadius: 'var(--ds-radius-sm)',
                      background: 'var(--ds-color-bg-soft)',
                      borderColor: 'var(--ds-color-border)',
                    }}
                  >
                    <Flex gap={10} align="center">
                      <RadarChartOutlined style={{ color: 'var(--ds-color-primary)' }} />
                      <div>
                        <Typography.Text strong>Score 89</Typography.Text>
                        <br />
                        <Typography.Text type="secondary">Match forte com stack e senioridade</Typography.Text>
                      </div>
                    </Flex>
                  </Card>
                </Col>
                <Col xs={24} md={12}>
                  <Card
                    size="small"
                    style={{
                      borderRadius: 'var(--ds-radius-sm)',
                      background: 'var(--ds-color-bg-soft)',
                      borderColor: 'var(--ds-color-border)',
                    }}
                  >
                    <Flex gap={10} align="center">
                      <CalendarOutlined style={{ color: 'var(--ds-color-success)' }} />
                      <div>
                        <Typography.Text strong>Proximo passo em 2 dias</Typography.Text>
                        <br />
                        <Typography.Text type="secondary">Email de retomada com portfolio</Typography.Text>
                      </div>
                    </Flex>
                  </Card>
                </Col>
              </Row>

              <Flex justify="end" gap={10} wrap>
                <DSActionButton emphasis="ghost">Descartar</DSActionButton>
                <DSActionButton emphasis="soft">Abrir contexto</DSActionButton>
                <DSActionButton emphasis="primary">Preparar candidatura</DSActionButton>
              </Flex>
            </Space>
          </Card>
        </Col>

        <Col xs={24} xl={9}>
          <Card
            style={{
              borderRadius: 'var(--ds-radius)',
              background:
                'linear-gradient(180deg, rgba(255,255,255,0.96), color-mix(in srgb, var(--ds-color-success-bg) 48%, white))',
              boxShadow: 'var(--ds-shadow-1)',
            }}
          >
            <Space direction="vertical" size={14} style={{ width: '100%' }}>
              <Typography.Text
                style={{
                  textTransform: 'uppercase',
                  letterSpacing: '0.12em',
                  color: 'var(--ds-color-success-text)',
                  fontWeight: 800,
                }}
              >
                Action lane
              </Typography.Text>
              {[
                'Atualizar portfolio com case de dashboard B2B',
                'Ajustar resumo para linguagem de produto e experimentacao',
                'Programar follow-up com CTA de disponibilidade',
              ].map((item) => (
                <Flex
                  key={item}
                  gap={12}
                  align="start"
                  style={{
                    padding: '14px 14px 14px 12px',
                    borderRadius: 'var(--ds-radius-sm)',
                    background: 'rgba(255,255,255,0.72)',
                    border: '1px solid var(--ds-color-border)',
                  }}
                >
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      background: 'var(--ds-color-success)',
                      marginTop: 6,
                      flexShrink: 0,
                    }}
                  />
                  <Typography.Text>{item}</Typography.Text>
                </Flex>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
    </Space>
  )
}

const meta = {
  title: 'Opta Design System/Templates/Composition',
  component: OptaCompositionPreview,
  parameters: {
    layout: 'padded',
  },
} satisfies Meta<typeof OptaCompositionPreview>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
