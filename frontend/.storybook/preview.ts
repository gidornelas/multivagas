import type { Preview } from '@storybook/react-vite'
import { createElement } from 'react'
import { App as AntApp, ConfigProvider } from 'antd'
import 'antd/dist/reset.css'
import '../src/design-system/theme.css'

import { dashboardAntTheme } from '../src/design-system/theme'

const preview: Preview = {
  decorators: [
    (Story) =>
      createElement(
        ConfigProvider,
        { theme: dashboardAntTheme },
        createElement(
          AntApp,
          null,
          createElement(
            'div',
            {
              style: {
                minHeight: '100vh',
                padding: 12,
                background:
                  'radial-gradient(circle at 12% 18%, var(--ds-color-primary-bg, #eef2ff) 0%, transparent 30%), radial-gradient(circle at 90% 5%, var(--ds-color-info-bg, #eff6ff) 0%, transparent 24%), var(--ds-color-bg-base, #fafbfc)',
              },
            },
            createElement(Story),
          ),
        ),
      ),
  ],
  parameters: {
    controls: {
      matchers: {
       color: /(background|color)$/i,
       date: /Date$/i,
      },
    },

    a11y: {
      // 'todo' - show a11y violations in the test UI only
      // 'error' - fail CI on a11y violations
      // 'off' - skip a11y checks entirely
      test: 'todo'
    }
  },
};

export default preview;