import {
  BellOutlined,
  CheckCircleOutlined,
  CompassOutlined,
  FileTextOutlined,
  FilterOutlined,
  FireOutlined,
  FunnelPlotOutlined,
  LineChartOutlined,
  PlusOutlined,
  RadarChartOutlined,
  SearchOutlined,
  SendOutlined,
  SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { Avatar, Card, Input, Progress, Space, Typography } from 'antd'

import { DSActionButton } from '../design-system/components/DSActionButton'
import { DSStatCard } from '../design-system/components/DSStatCard'
import { DSStatusPill } from '../design-system/components/DSStatusPill'
import './OptaDashboard.css'

type QueueItem = {
  title: string
  company: string
  score: number
  status: 'aplicada' | 'entrevista' | 'processo' | 'recusada'
  nextStep: string
}

const queueItems: QueueItem[] = [
  {
    title: 'Senior Product Designer',
    company: 'Trybe',
    score: 94,
    status: 'entrevista',
    nextStep: 'Entrevista tecnica amanha, 10:30',
  },
  {
    title: 'Design Systems Lead',
    company: 'Conta Azul',
    score: 89,
    status: 'processo',
    nextStep: 'Enviar portfolio ajustado ate sexta',
  },
  {
    title: 'Product Designer II',
    company: 'Gupy',
    score: 77,
    status: 'aplicada',
    nextStep: 'Follow-up em 4 dias',
  },
]

const capturedRoles = [
  { company: 'Nubank', role: 'Staff Product Designer', location: 'Hibrido', score: 96 },
  { company: 'Pismo', role: 'Design Ops Manager', location: 'Remoto', score: 91 },
  { company: 'Hotmart', role: 'Lead UX Strategist', location: 'Brasil', score: 88 },
]

const activityItems = [
  '42 novas vagas analisadas nas ultimas 24h',
  '6 candidaturas movidas para a fase de entrevista',
  '2 follow-ups prontos para disparo hoje',
]

const navigationItems = [
  { icon: <CompassOutlined />, label: 'Overview', active: true },
  { icon: <RadarChartOutlined />, label: 'Pipeline' },
  { icon: <FileTextOutlined />, label: 'Curriculos' },
  { icon: <FunnelPlotOutlined />, label: 'Captura' },
  { icon: <LineChartOutlined />, label: 'Analytics' },
  { icon: <SettingOutlined />, label: 'Configuracoes' },
]

function OptaDashboard() {
  return (
    <div className="opta-shell">
      <aside className="opta-sidebar">
        <div className="opta-brand">
          <img className="opta-brand-wordmark" src="/brand/opta-wordmark.png" alt="Opta" />
          <Typography.Text className="opta-brand-tag">Vagas inteligentes</Typography.Text>
        </div>

        <nav className="opta-nav" aria-label="Principal">
          {navigationItems.map((item) => (
            <button
              key={item.label}
              className={`opta-nav-item${item.active ? ' is-active' : ''}`}
              type="button"
            >
              <span className="opta-nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <Card className="opta-sidebar-card" bordered={false}>
          <Space direction="vertical" size={10}>
            <Typography.Text className="opta-sidebar-card-kicker">
              Signal room
            </Typography.Text>
            <Typography.Title level={4} className="opta-sidebar-card-title">
              3 vagas com score acima de 90 esperando decisao.
            </Typography.Title>
            <Typography.Paragraph className="opta-sidebar-card-copy">
              A cabine da semana destaca as capturas com maior potencial e menor tempo de resposta.
            </Typography.Paragraph>
            <DSActionButton emphasis="primary" icon={<FireOutlined />}>
              Abrir prioridade
            </DSActionButton>
          </Space>
        </Card>
      </aside>

      <main className="opta-main">
        <header className="opta-topbar">
          <div>
            <Typography.Text className="opta-topbar-kicker">Opta cockpit</Typography.Text>
            <Typography.Title level={2} className="opta-topbar-title">
              Painel de decisao e cadencia
            </Typography.Title>
          </div>

          <div className="opta-topbar-actions">
            <Input
              className="opta-search"
              prefix={<SearchOutlined />}
              placeholder="Buscar vaga, empresa ou criterio"
            />
            <DSActionButton emphasis="ghost" icon={<BellOutlined />}>
              Alertas
            </DSActionButton>
            <Avatar size={42} className="opta-avatar">
              OP
            </Avatar>
          </div>
        </header>

        <section className="opta-hero">
          <div className="opta-hero-copy">
            <Typography.Text className="opta-hero-kicker">
              recruitment orchestration
            </Typography.Text>
            <Typography.Title level={1} className="opta-hero-title ds-display">
              O novo sistema visual da Opta entrou no cockpit do produto.
            </Typography.Title>
            <Typography.Paragraph className="opta-hero-text">
              A interface agora trabalha contraste entre cabine escura, superficies editoriais claras e
              sinais fortes para prioridade, match e proximos passos.
            </Typography.Paragraph>

            <div className="opta-hero-actions">
              <DSActionButton emphasis="primary" icon={<PlusOutlined />}>
                Nova captura
              </DSActionButton>
              <DSActionButton emphasis="soft" icon={<FilterOutlined />}>
                Refinar criterios
              </DSActionButton>
              <DSActionButton emphasis="ghost">Ver historico</DSActionButton>
            </div>
          </div>

          <Card className="opta-hero-panel" bordered={false}>
            <div className="opta-hero-panel-header">
              <div>
                <Typography.Text className="opta-panel-kicker">Decision board</Typography.Text>
                <Typography.Title level={3} className="opta-panel-title">
                  Semana em foco
                </Typography.Title>
              </div>
              <DSStatusPill status="entrevista" label="momento forte" />
            </div>

            <div className="opta-signal-list">
              {activityItems.map((item) => (
                <div key={item} className="opta-signal-item">
                  <span className="opta-signal-dot" />
                  <Typography.Text>{item}</Typography.Text>
                </div>
              ))}
            </div>

            <div className="opta-signal-meter">
              <div className="opta-signal-meter-copy">
                <Typography.Text className="opta-panel-kicker">Cadencia semanal</Typography.Text>
                <Typography.Text strong>78% do plano executado</Typography.Text>
              </div>
              <Progress
                percent={78}
                showInfo={false}
                strokeColor="#F1873E"
                trailColor="rgba(255,255,255,0.08)"
              />
            </div>
          </Card>
        </section>

        <section className="opta-stats-grid">
          <DSStatCard
            label="Capturas priorizadas"
            value={42}
            helper="+12 desde ontem"
            percent={84}
            caption="Pipeline de alta aderencia"
            tone="primary"
          />
          <DSStatCard
            label="Em entrevista"
            value={8}
            helper="ritmo consistente"
            percent={66}
            caption="Slots ativos esta semana"
            tone="success"
          />
          <DSStatCard
            label="Follow-ups prontos"
            value={14}
            helper="janela de envio aberta"
            percent={72}
            caption="Textos e anexos organizados"
            tone="info"
          />
          <DSStatCard
            label="Risco de perda"
            value={3}
            helper="agir hoje"
            percent={28}
            caption="Vagas sem resposta ha 5 dias"
            tone="warning"
          />
        </section>

        <section className="opta-content-grid">
          <Card className="opta-surface-card" bordered={false}>
            <div className="opta-section-head">
              <div>
                <Typography.Text className="opta-section-kicker">Priority queue</Typography.Text>
                <Typography.Title level={3} className="opta-section-title">
                  Pipeline em movimento
                </Typography.Title>
              </div>
              <DSActionButton emphasis="soft" icon={<TeamOutlined />}>
                Ver todas
              </DSActionButton>
            </div>

            <div className="opta-queue">
              {queueItems.map((item) => (
                <article key={`${item.company}-${item.title}`} className="opta-queue-item">
                  <div className="opta-queue-main">
                    <div>
                      <Typography.Title level={4} className="opta-queue-title">
                        {item.title}
                      </Typography.Title>
                      <Typography.Text className="opta-queue-company">
                        {item.company}
                      </Typography.Text>
                    </div>
                    <div className="opta-queue-score">{item.score}</div>
                  </div>

                  <div className="opta-queue-meta">
                    <DSStatusPill status={item.status} />
                    <Typography.Text className="opta-queue-step">{item.nextStep}</Typography.Text>
                  </div>
                </article>
              ))}
            </div>
          </Card>

          <Card className="opta-surface-card opta-dark-card" bordered={false}>
            <div className="opta-section-head">
              <div>
                <Typography.Text className="opta-section-kicker dark">Radar Opta</Typography.Text>
                <Typography.Title level={3} className="opta-section-title dark">
                  Vagas capturadas com maior aderencia
                </Typography.Title>
              </div>
            </div>

            <div className="opta-captured-list">
              {capturedRoles.map((item) => (
                <div key={`${item.company}-${item.role}`} className="opta-captured-item">
                  <div>
                    <Typography.Text className="opta-captured-company">
                      {item.company}
                    </Typography.Text>
                    <Typography.Title level={4} className="opta-captured-role">
                      {item.role}
                    </Typography.Title>
                    <Typography.Text className="opta-captured-location">
                      {item.location}
                    </Typography.Text>
                  </div>
                  <span className="opta-captured-score">{item.score}</span>
                </div>
              ))}
            </div>
          </Card>
        </section>

        <section className="opta-bottom-grid">
          <Card className="opta-surface-card" bordered={false}>
            <div className="opta-section-head">
              <div>
                <Typography.Text className="opta-section-kicker">Execution</Typography.Text>
                <Typography.Title level={3} className="opta-section-title">
                  Proximas acoes
                </Typography.Title>
              </div>
            </div>

            <div className="opta-task-list">
              <div className="opta-task-item">
                <CheckCircleOutlined />
                <div>
                  <Typography.Text strong>Atualizar portfolio para Conta Azul</Typography.Text>
                  <Typography.Paragraph>
                    Reforcar cases de design system e rollout cross-team.
                  </Typography.Paragraph>
                </div>
              </div>
              <div className="opta-task-item">
                <SendOutlined />
                <div>
                  <Typography.Text strong>Disparar follow-up para Gupy</Typography.Text>
                  <Typography.Paragraph>Janela recomendada entre 09:00 e 11:00.</Typography.Paragraph>
                </div>
              </div>
              <div className="opta-task-item">
                <FileTextOutlined />
                <div>
                  <Typography.Text strong>Gerar CV adaptado para Pismo</Typography.Text>
                  <Typography.Paragraph>
                    Enfase em Design Ops, leadership e metricas.
                  </Typography.Paragraph>
                </div>
              </div>
            </div>
          </Card>

          <Card className="opta-surface-card" bordered={false}>
            <div className="opta-section-head">
              <div>
                <Typography.Text className="opta-section-kicker">System notes</Typography.Text>
                <Typography.Title level={3} className="opta-section-title">
                  Principios da nova linguagem
                </Typography.Title>
              </div>
            </div>

            <div className="opta-principles">
              <div className="opta-principle">
                <span>01</span>
                <Typography.Text>O laranja sinaliza acao, decisao e prioridade.</Typography.Text>
              </div>
              <div className="opta-principle">
                <span>02</span>
                <Typography.Text>
                  O turquesa organiza saude do fluxo e confirma sinais positivos.
                </Typography.Text>
              </div>
              <div className="opta-principle">
                <span>03</span>
                <Typography.Text>
                  Cabines escuras recebem foco estrategico; blocos claros cuidam da leitura.
                </Typography.Text>
              </div>
            </div>
          </Card>
        </section>
      </main>
    </div>
  )
}

export default OptaDashboard
