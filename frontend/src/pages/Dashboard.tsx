import {
  Layout,
  Row,
  Col,
  Card,
  Statistic,
  Button,
  Tag,
  Input,
  Select,
  Checkbox,
  Radio,
  Slider,
  Switch,
  Badge,
  Divider,
  Modal,
} from 'antd';
import {
  CheckCircleOutlined,
} from '@ant-design/icons';
import { DashboardThemeProvider } from '@/theme/DashboardThemeProvider';
import { useState } from 'react';

const { Content } = Layout;

const DashboardContent = () => {
  const [sliderValue, setSliderValue] = useState(60);
  const [switchStates, setSwitchStates] = useState({
    apple: true,
    banana: false,
    orange: true,
  });

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#E8E3D3',
        padding: '40px 24px',
      }}
    >
      <Content style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Showcase Modal */}
        <Modal
          title="🌿 Ant Design Theme Showcase"
          open={true}
          footer={null}
          onCancel={() => {}}
          width={700}
          bodyStyle={{ paddingBottom: 32 }}
          closeIcon={null}
        >
          <p style={{ color: 'rgba(46, 58, 107, 0.65)', marginBottom: 24 }}>
            Ant Design use CSS-in-JS technology to provide dynamic & mix theme ability. And which use
            component level CSS-in-JS solution get your application a better performance.
          </p>

          {/* Input Section */}
          <Input placeholder="Info Text" style={{ marginBottom: 16 }} />

          {/* Select and Tags */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col flex="100px">
              <Select
                style={{ width: '100%' }}
                placeholder="Dropdown"
                options={[
                  { label: 'Option 1', value: '1' },
                  { label: 'Option 2', value: '2' },
                ]}
              />
            </Col>
            <Col flex="auto">
              <Select
                mode="multiple"
                placeholder="Select tags"
                style={{ width: '100%' }}
                options={[
                  { label: 'Apple', value: 'apple' },
                  { label: 'Banana', value: 'banana' },
                  { label: 'Orange', value: 'orange' },
                ]}
                defaultValue={['apple', 'banana']}
              />
            </Col>
          </Row>

          {/* Date and Tags Section */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col flex="120px">
              <Input type="date" placeholder="Select date" />
            </Col>
            <Col flex="auto" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Tag closable>Apple</Tag>
              <Tag closable>Banana</Tag>
            </Col>
          </Row>

          {/* Progress */}
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: '#2E3A6B' }}>Progress</span>
              <span style={{ fontSize: 12, color: '#2E3A6B' }}>60%</span>
            </div>
            <Slider
              value={sliderValue}
              onChange={setSliderValue}
              style={{ marginBottom: 24 }}
            />
          </div>

          {/* Status Badges */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col>
              <Badge
                count={
                  <CheckCircleOutlined
                    style={{ color: '#A9C27D', fontSize: 20 }}
                  />
                }
                text="Finished"
              />
            </Col>
            <Col>
              <Badge
                count={2}
                style={{ backgroundColor: '#4F6F2F' }}
                text="In Progress"
              />
            </Col>
            <Col>
              <span style={{ color: 'rgba(46, 58, 107, 0.45)' }}>3 Waiting</span>
            </Col>
          </Row>

          <Divider />

          {/* Buttons */}
          <Row gutter={8} style={{ marginBottom: 24 }}>
            <Col>
              <Button type="primary">Primary</Button>
            </Col>
            <Col>
              <Button danger>Danger</Button>
            </Col>
            <Col>
              <Button>Default</Button>
            </Col>
            <Col>
              <Button variant="dashed">Dashed</Button>
            </Col>
          </Row>

          {/* Toggles and Checkboxes */}
          <Row gutter={[24, 16]} style={{ marginBottom: 24 }}>
            <Col>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Switch
                  checked={switchStates.apple}
                  onChange={(checked) =>
                    setSwitchStates({ ...switchStates, apple: checked })
                  }
                />
                <span>Apple</span>
              </div>
            </Col>
            <Col>
              <Checkbox defaultChecked>Apple</Checkbox>
            </Col>
            <Col>
              <Checkbox>Banana</Checkbox>
            </Col>
            <Col>
              <Checkbox>Orange</Checkbox>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col>
              <Radio.Group
                options={[
                  { label: 'A', value: 'a' },
                  { label: 'B', value: 'b' },
                  { label: 'C', value: 'c' },
                ]}
              />
            </Col>
            <Col>
              <Radio.Group
                options={[
                  { label: 'Daily', value: 'daily' },
                  { label: 'Weekly', value: 'weekly' },
                  { label: 'Monthly', value: 'monthly' },
                ]}
              />
            </Col>
          </Row>
        </Modal>

        {/* Stats Cards */}
        <Row gutter={[24, 24]} style={{ marginTop: 40 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card
              bordered={false}
              style={{
                background: '#F1F7E8',
                boxShadow: '0 3px 10px 0 rgba(46, 58, 107, 0.06)',
              }}
            >
              <Statistic
                title="Total de Vagas"
                value={124}
                valueStyle={{ color: '#4F6F2F', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card
              bordered={false}
              style={{
                background: '#F9F7F2',
                boxShadow: '0 3px 10px 0 rgba(46, 58, 107, 0.06)',
              }}
            >
              <Statistic
                title="Candidaturas"
                value={18}
                valueStyle={{ color: '#9C9263', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card
              bordered={false}
              style={{
                background: '#E9EFF5',
                boxShadow: '0 3px 10px 0 rgba(46, 58, 107, 0.06)',
              }}
            >
              <Statistic
                title="Em Entrevista"
                value={5}
                valueStyle={{ color: '#7E98B2', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card
              bordered={false}
              style={{
                background: '#E9ECF3',
                boxShadow: '0 3px 10px 0 rgba(46, 58, 107, 0.06)',
              }}
            >
              <Statistic
                title="Taxa de Conversão"
                value={27.8}
                suffix="%"
                valueStyle={{ color: '#2E3A6B', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
        </Row>
      </Content>
    </div>
  );
};

export const Dashboard = () => {
  return (
    <DashboardThemeProvider>
      <DashboardContent />
    </DashboardThemeProvider>
  );
};

export default Dashboard;
