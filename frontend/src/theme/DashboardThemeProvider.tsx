import { App, ConfigProvider } from 'antd'
import type { ReactNode } from 'react'

import { dashboardAntTheme } from '../design-system/theme'
import '../design-system/theme.css'

interface DashboardThemeProviderProps {
  children: ReactNode
}

export const DashboardThemeProvider = ({ children }: DashboardThemeProviderProps) => {
  return (
    <ConfigProvider theme={dashboardAntTheme}>
      <App>
        {children}
      </App>
    </ConfigProvider>
  )
}

export default DashboardThemeProvider
