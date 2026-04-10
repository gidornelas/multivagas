import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { ApplicationStatusCard } from '../components/ApplicationStatusCard'

const meta = {
  title: 'Jobs/ApplicationStatusCard',
  component: ApplicationStatusCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  args: {
    company: 'Framework System',
    role: 'Designer UX/UI',
    location: 'Remoto - Brasil',
    score: 87,
    appliedAt: '09/04/2026',
    followUpDate: '16/04/2026',
    status: 'aplicada',
    onFollowUp: fn(),
  },
} satisfies Meta<typeof ApplicationStatusCard>

export default meta

type Story = StoryObj<typeof meta>

export const Aplicada: Story = {}

export const Entrevista: Story = {
  args: {
    status: 'entrevista',
    score: 94,
  },
}

export const EmAndamento: Story = {
  args: {
    status: 'em-andamento',
    score: 73,
  },
}
