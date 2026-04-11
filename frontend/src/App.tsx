import OptaDashboard from './pages/OptaDashboard'
import { DashboardThemeProvider } from './theme/DashboardThemeProvider'

function App() {
  return (
    <DashboardThemeProvider>
      <OptaDashboard />
    </DashboardThemeProvider>
  )
}

export default App
