import React, { useState, useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist';
import { Button, Alert, Space, Typography } from 'antd';
import { generateChartConfig, detectChartType } from '../utils/chartSelector';  // 添加 detectChartType

const { Text } = Typography;

const DataVisualization = ({ data, type = 'auto', title = '数据可视化' }) => {
  const [showVisualization, setShowVisualization] = useState(false);
  const [suggestedType, setSuggestedType] = useState(null);
  const chartRef = useRef(null);

  // 添加可视化建议函数
  const getVisualizationSuggestion = () => {
    switch (suggestedType) {
      case 'line': return '时间序列数据适合使用折线图展示';
      case 'bar': return '分类统计数据适合使用柱状图展示';
      case 'pie': return '占比数据适合使用饼图展示';
      case 'scatter': return '数值关系适合使用散点图展示';
      case 'histogram': return '分布数据适合使用直方图展示';
      default: return '数据适合使用表格形式展示';
    }
  };

  useEffect(() => {
    if (!data || data.length === 0) return;
    const chartType = type === 'auto' ? detectChartType(data) : type;
    setSuggestedType(chartType);
    setShowVisualization(false);
  }, [data, type]);

  useEffect(() => {
    if (!showVisualization || !suggestedType || !chartRef.current) return;
    
    const plotConfig = generateChartConfig(data, suggestedType, title);
    Plotly.newPlot(chartRef.current, plotConfig.data, plotConfig.layout);

    return () => {
      if (chartRef.current) {
        Plotly.purge(chartRef.current);
      }
    };
  }, [data, showVisualization, suggestedType, title]);

  return (
    <div className="visualization-wrapper">
      {!showVisualization && suggestedType && (
        <Alert
          message="可视化建议"
          description={
            <Space direction="vertical">
              <Text>{getVisualizationSuggestion()}</Text>
              <Button type="primary" onClick={() => setShowVisualization(true)}>
                生成图表
              </Button>
            </Space>
          }
          type="info"
          showIcon
        />
      )}

      {showVisualization && (
        <div ref={chartRef} className="chart-container" />
      )}
    </div>
  );
};

export default DataVisualization;