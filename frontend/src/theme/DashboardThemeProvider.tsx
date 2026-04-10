import { ConfigProvider, theme, App } from 'antd';
import type { ReactNode } from 'react';

interface DashboardThemeProviderProps {
  children: ReactNode;
}

export const DashboardThemeProvider = ({ children }: DashboardThemeProviderProps) => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#4F6F2F',
          colorSuccess: '#A9C27D',
          colorWarning: '#E8E3D3',
          colorError: '#2E3A6B',
          colorInfo: '#7E98B2',
          colorTextBase: '#2E3A6B',
          colorBgBase: '#E8E3D3',
          colorPrimaryBg: '#DDE8CC',
          colorPrimaryBgHover: '#C6D9AA',
          colorPrimaryBorder: '#A9C27D',
          colorPrimaryBorderHover: '#4F6F2F',
          colorPrimaryHover: '#3E5924',
          colorPrimaryActive: '#2E3F1B',
          colorPrimaryText: '#4F6F2F',
          colorPrimaryTextHover: '#3E5924',
          colorPrimaryTextActive: '#2E3F1B',
          colorSuccessBg: '#F1F7E8',
          colorSuccessBgHover: '#E2F0D1',
          colorSuccessBorder: '#C6D9AA',
          colorSuccessBorderHover: '#A9C27D',
          colorSuccessHover: '#8BA55E',
          colorSuccessActive: '#6B8249',
          colorSuccessText: '#4F6F2F',
          colorSuccessTextHover: '#3E5924',
          colorSuccessTextActive: '#2E3F1B',
          colorWarningBg: '#F9F7F2',
          colorWarningBgHover: '#F3F0E6',
          colorWarningBorder: '#E8E3D3',
          colorWarningBorderHover: '#D5CDB7',
          colorWarningHover: '#C2B89B',
          colorWarningActive: '#AFA57F',
          colorWarningText: '#9C9263',
          colorWarningTextHover: '#7E7350',
          colorWarningTextActive: '#60553D',
          colorErrorBg: '#E9ECF3',
          colorErrorBgHover: '#D4DBE8',
          colorErrorBorder: '#BEC9DB',
          colorErrorBorderHover: '#A4B5CE',
          colorErrorHover: '#8BA1C0',
          colorErrorActive: '#7088AC',
          colorErrorText: '#2E3A6B',
          colorErrorTextHover: '#252E55',
          colorErrorTextActive: '#1C2240',
          colorInfoBg: '#E9EFF5',
          colorInfoBgHover: '#D4E0EC',
          colorInfoBorder: '#BFD0E0',
          colorInfoBorderHover: '#A4BBD1',
          colorInfoHover: '#8BA6C2',
          colorInfoActive: '#7091B3',
          colorInfoText: '#7E98B2',
          colorInfoTextHover: '#647F9F',
          colorInfoTextActive: '#4F668B',
          colorText: 'rgba(46, 58, 107, 0.88)',
          colorTextSecondary: 'rgba(46, 58, 107, 0.65)',
          colorTextTertiary: 'rgba(46, 58, 107, 0.45)',
          colorTextQuaternary: 'rgba(46, 58, 107, 0.25)',
          colorTextDisabled: 'rgba(46, 58, 107, 0.25)',
          colorBgContainer: '#F3F1E8',
          colorBgElevated: '#FFFFFF',
          colorBgLayout: '#E8E3D3',
          colorBgSpotlight: 'rgba(46, 58, 107, 0.85)',
          colorBgMask: 'rgba(46, 58, 107, 0.45)',
          colorBorder: '#D5CDB7',
          colorBorderSecondary: '#E8E3D3',
          borderRadius: 10,
          borderRadiusXS: 3,
          borderRadiusSM: 6,
          borderRadiusLG: 14,
          padding: 18,
          paddingSM: 14,
          paddingLG: 26,
          margin: 18,
          marginSM: 14,
          marginLG: 26,
          boxShadow: '0 3px 10px 0 rgba(46, 58, 107, 0.06)',
          boxShadowSecondary: '0 5px 14px 0 rgba(46, 58, 107, 0.08)',
        },
      }}
    >
      <App>
        {children}
      </App>
    </ConfigProvider>
  );
};

export default DashboardThemeProvider;
