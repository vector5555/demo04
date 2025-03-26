import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Typography, Rate, Collapse, Space } from 'antd';  // Add Space
import { EditOutlined } from '@ant-design/icons';
import DataVisualization from './DataVisualization';
import { detectChartType } from '../utils/chartSelector';

const { Text } = Typography;
const { Panel } = Collapse;
const PAGE_SIZE = 50; // 每页显示的数据条数

function MessageItem({ message, index, messages, onEdit, onRate }) {
  const [displayData, setDisplayData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (message.result && Array.isArray(message.result)) {
      setDisplayData(message.result.slice(0, PAGE_SIZE));
      setCurrentPage(1);
    }
  }, [message.result]);

  const handleScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollHeight - scrollTop === clientHeight) {
      loadMoreData();
    }
  };

  const loadMoreData = () => {
    const nextData = message.result.slice(0, (currentPage + 1) * PAGE_SIZE);
    setDisplayData(nextData);
    setCurrentPage(prev => prev + 1);
  };

  if (message.type === 'user') {
    return (
      <div className="user-message">
        <Text>{message.content}</Text>
        <Text type="secondary" className="message-time">{message.timestamp}</Text>
      </div>
    );
  }

  return (
    <div className="system-message">
      <Collapse defaultActiveKey={['sql']}>
        <Panel 
          header={message.isEdited ? "编辑后的 SQL" : "AI 生成的 SQL"} 
          key="sql"
          extra={
            !message.isEdited && (
              <Button 
                icon={<EditOutlined />} 
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(message.sql, messages[index - 1]?.content);
                }}
              >
                编辑
              </Button>
            )
          }
        >
          <pre>{message.sql}</pre>
          {message.isEdited && (
            <Text type="secondary">编辑时间: {message.editTime}</Text>
          )}
        </Panel>
      </Collapse>
      
      {message.error ? (
        <Alert
          message="执行错误"
          description={message.error}
          type="error"
          showIcon
        />
      ) : (
        message.result && Array.isArray(message.result) && (
          <>
            <Collapse defaultActiveKey={['data', 'visualization']}>
              <Panel header="查询结果" key="data">
                {message.result.length > 0 ? (
                  <div className="result-section">
                    <div className="data-stats">
                      <Text>总记录数：{message.result.length}</Text>
                      <Text>当前显示：第 {1} 条 至 第 {displayData.length} 条</Text>
                    </div>
                    <div className="table-wrapper" onScroll={handleScroll}>
                      <table>
                        <thead>
                          <tr>
                            <th className="index-column">#</th>
                            {Object.keys(message.result[0]).map(key => (
                              <th key={key}>{key}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {displayData.map((row, idx) => (
                            <tr key={idx}>
                              <td className="index-column">{idx + 1}</td>
                              {Object.values(row).map((value, i) => (
                                <td key={i}>{value}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <Alert
                    message="查询成功"
                    description="该查询没有返回任何数据"
                    type="info"
                    showIcon
                  />
                )}
              </Panel>
              
              {message.result.length > 0 && (
                <Panel header="数据可视化" key="visualization">
                  <div className="visualization-container">
                    <DataVisualization 
                      data={message.result}
                      type={detectChartType(message.result)}
                      title={message.isEdited ? "编辑后查询结果可视化" : "查询结果可视化"}
                    />
                  </div>
                </Panel>
              )}
            </Collapse>

            {!message.rated && (
              <div className="feedback-section">
                <Space direction="vertical" align="center" style={{ width: '100%', marginTop: '16px' }}>
                  <Text>这个查询结果符合你的预期吗？</Text>
                  <Rate onChange={(value) => onRate(index, value)} />
                </Space>
              </div>
            )}
          </>
        )
      )}
      <Text type="secondary" className="message-time">{message.timestamp}</Text>
    </div>
  );
}

export default MessageItem;