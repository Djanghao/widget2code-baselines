import { Modal, Statistic, Row, Col, Progress, Table, Typography, Spin, Alert } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;

export default function CheckRunModal({ open, onClose, run, data, loading, error }) {
  if (!data && !loading && !error) {
    return null;
  }

  const total = data?.total || 0;
  // Success now counts only items with PNGs
  const pngRendered = data?.withPng || 0;
  const success = typeof data?.success_png === 'number' ? data.success_png : pngRendered;
  const requestFailed = data?.request_failed || 0;
  const responseNone = data?.response_none || 0;
  const contentEmpty = data?.content_empty || 0;
  const missingOutput = data?.missing_output || 0;
  const invalidHtml = data?.invalid_html || 0;
  const invalidMeta = data?.invalid_meta || 0;

  const pngTotal = data?.pngTotal || total;
  const successRate = total > 0 ? (success / total) * 100 : 0;
  const failureCount = requestFailed + responseNone + contentEmpty + missingOutput + invalidHtml + invalidMeta;

  const errorCategories = [
    {
      key: 'request_failed',
      label: 'Request Failed',
      count: requestFailed,
      description: 'API request threw exception',
      color: '#ff4d4f'
    },
    {
      key: 'response_none',
      label: 'Response None',
      count: responseNone,
      description: 'Response object is None',
      color: '#ff7a45'
    },
    {
      key: 'content_empty',
      label: 'Content Empty',
      count: contentEmpty,
      description: 'Response content is empty or None',
      color: '#ffa940'
    },
    {
      key: 'missing_output',
      label: 'Missing Output',
      count: missingOutput,
      description: 'Output file (.html/.jsx) not found',
      color: '#ffc53d'
    },
    {
      key: 'invalid_html',
      label: 'Invalid HTML',
      count: invalidHtml,
      description: 'HTML is invalid or incomplete',
      color: '#9254de'
    },
    {
      key: 'invalid_meta',
      label: 'Invalid Meta',
      count: invalidMeta,
      description: 'Meta.json file is invalid',
      color: '#d4380d'
    }
  ];

  const columns = [
    {
      title: 'Category',
      dataIndex: 'label',
      key: 'label',
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 600, color: record.color }}>{text}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.description}</Text>
        </div>
      )
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      align: 'right',
      width: 100,
      render: (count) => <Text strong>{count}</Text>
    },
    {
      title: 'Percentage',
      key: 'percentage',
      align: 'right',
      width: 120,
      render: (_, record) => {
        const percentage = total > 0 ? (record.count / total) * 100 : 0;
        return <Text>{percentage.toFixed(1)}%</Text>;
      }
    }
  ];

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={800}
      centered
      title={`Check Results: ${run || 'Loading...'}`}
    >
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
          <Spin size="large" />
        </div>
      ) : error ? (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
        />
      ) : (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'stretch', marginBottom: 24 }}>
            <div style={{ flex: '0 0 auto' }}>
              <Statistic
                title="Total Tasks"
                value={total}
                valueStyle={{ color: '#1677ff' }}
              />
            </div>
            <div style={{ flex: '0 0 auto' }}>
              <Statistic
                title="Success"
                value={success}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </div>
            <div style={{ flex: '0 0 auto' }}>
              <Statistic
                title="PNG Rendered"
                value={pngRendered}
                suffix={pngTotal > 0 ? ` / ${pngTotal}` : undefined}
                valueStyle={{ color: '#13c2c2' }}
              />
            </div>
            <div style={{ flex: '0 0 auto' }}>
              <Statistic
                title="Content Empty"
                value={contentEmpty}
                valueStyle={{ color: '#faad14' }}
              />
            </div>
            <div style={{ flex: '0 0 auto' }}>
              <Statistic
                title="Invalid HTML"
                value={invalidHtml}
                valueStyle={{ color: '#9254de' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>Success Rate</Text>
            <Progress
              percent={successRate}
              strokeColor={{
                '0%': successRate >= 90 ? '#52c41a' : successRate >= 70 ? '#faad14' : '#ff4d4f',
                '100%': successRate >= 90 ? '#73d13d' : successRate >= 70 ? '#ffc53d' : '#ff7875'
              }}
              status={successRate >= 90 ? 'success' : successRate >= 70 ? 'normal' : 'exception'}
            />
          </div>

          {failureCount > 0 && (
            <div>
              <Title level={5} style={{ marginBottom: 12 }}>Failure Breakdown</Title>
              <Table
                dataSource={errorCategories.filter(cat => cat.count > 0)}
                columns={columns}
                pagination={false}
                size="small"
                rowKey="key"
              />
            </div>
          )}

          {failureCount === 0 && (
            <Alert
              message="All tasks completed successfully!"
              type="success"
              showIcon
              icon={<CheckCircleOutlined />}
            />
          )}
        </div>
      )}
    </Modal>
  );
}
