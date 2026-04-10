import type { ThemeConfig } from 'antd'

import { dashboardTokens } from './tokens'

export const dashboardAntTheme: ThemeConfig = {
  token: {
    colorPrimary: dashboardTokens.colorPrimary,
    colorSuccess: dashboardTokens.colorSuccess,
    colorWarning: dashboardTokens.colorWarning,
    colorError: dashboardTokens.colorError,
    colorInfo: dashboardTokens.colorInfo,
    colorTextBase: dashboardTokens.colorTextBase,
    colorBgBase: dashboardTokens.colorBgBase,
    colorText: dashboardTokens.colorText,
    colorTextSecondary: dashboardTokens.colorTextSecondary,
    colorBgContainer: dashboardTokens.colorBgContainer,
    colorBgLayout: dashboardTokens.colorBgLayout,
    colorBorder: dashboardTokens.colorBorder,
    borderRadius: dashboardTokens.borderRadius,
    borderRadiusSM: dashboardTokens.borderRadiusSM,
    borderRadiusLG: dashboardTokens.borderRadiusLG,
    boxShadow: dashboardTokens.boxShadow,
    boxShadowSecondary: dashboardTokens.boxShadowSecondary,
    padding: dashboardTokens.padding,
    paddingSM: dashboardTokens.paddingSM,
    paddingLG: dashboardTokens.paddingLG,
    margin: dashboardTokens.margin,
    marginSM: dashboardTokens.marginSM,
    marginLG: dashboardTokens.marginLG,
    fontFamily: 'Plus Jakarta Sans, Segoe UI, sans-serif',
  },
}
