import { Button, Card, Flex, Progress, Space, Tag, Typography } from 'antd'
import { CalendarOutlined, SendOutlined } from '@ant-design/icons'

export type ApplicationStatusCardProps = {
  company: string
  role: string
  location: string
  score: number
  appliedAt: string
  followUpDate: string
  status?: 'aplicada' | 'entrevista' | 'em-andamento'
  onFollowUp?: () => void
}

const statusColorMap: Record<NonNullable<ApplicationStatusCardProps['status']>, string> = {
  aplicada: 'processing',
  entrevista: 'success',
  'em-andamento': 'warning',
}

export function ApplicationStatusCard({
  company,
  role,
  location,
  score,
  appliedAt,
  followUpDate,
  status = 'aplicada',
  onFollowUp,
}: ApplicationStatusCardProps) {
  return (
    <Card
      title={
        <Flex align="center" justify="space-between" wrap>
          <Typography.Text strong>{company}</Typography.Text>
          <Tag color={statusColorMap[status]}>{status}</Tag>
        </Flex>
      }
      style={{ width: '100%', maxWidth: 520 }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <Typography.Title level={4} style={{ marginBottom: 4 }}>
            {role}
          </Typography.Title>
          <Typography.Text type="secondary">{location}</Typography.Text>
        </div>

        <div>
          <Flex align="center" justify="space-between">
            <Typography.Text>Match da vaga</Typography.Text>
            <Typography.Text strong>{score}%</Typography.Text>
          </Flex>
          <Progress percent={score} status={score >= 80 ? 'success' : 'active'} />
        </div>

        <Flex align="center" justify="space-between" wrap gap={8}>
          <Space>
            <CalendarOutlined />
            <Typography.Text type="secondary">Aplicada em {appliedAt}</Typography.Text>
          </Space>
          <Typography.Text>Follow-up: {followUpDate}</Typography.Text>
        </Flex>

        <Button type="primary" icon={<SendOutlined />} onClick={onFollowUp}>
          Preparar follow-up
        </Button>
      </Space>
    </Card>
  )
}
