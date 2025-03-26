export const detectChartType = (data) => {
  if (!data || data.length === 0) return 'table';
  
  const columns = Object.keys(data[0]);
  const sampleRow = data[0];
  
  // 检查时间序列
  const hasTimeColumn = columns.some(col => 
    isTimeFormat(sampleRow[col]) || col.toLowerCase().includes('time')
  );
  if (hasTimeColumn) return 'line';
  
  // 检查分类数据
  const categoricalColumns = columns.filter(col => 
    typeof sampleRow[col] === 'string' || typeof sampleRow[col] === 'boolean'
  );
  const numericColumns = columns.filter(col => 
    typeof sampleRow[col] === 'number'
  );
  
  if (categoricalColumns.length === 1 && numericColumns.length === 1) {
    return data.length > 10 ? 'bar' : 'pie';
  }
  
  // 检查相关性
  if (numericColumns.length >= 2) {
    return 'scatter';
  }
  
  // 检查分布
  if (numericColumns.length === 1 && data.length > 30) {
    return 'histogram';
  }
  
  // 默认表格显示
  return 'table';
};

// 辅助函数：检查是否为时间格式
const isTimeFormat = (value) => {
  if (typeof value !== 'string') return false;
  return !isNaN(Date.parse(value));
};

// 添加图表配置生成函数
export const generateChartConfig = (data, type, title) => {
  const columns = Object.keys(data[0]);
  const config = {
    data: [],
    layout: {
      title: title || '数据可视化',
      font: { family: 'Microsoft YaHei' },  // 使用中文字体
      showlegend: true,
      legend: { font: { family: 'Microsoft YaHei' } }
    }
  };

  switch (type) {
    case 'line':
      config.data = [{
        x: data.map(row => row[columns[0]]),
        y: data.map(row => row[columns[1]]),
        type: 'line',
        name: '趋势变化'
      }];
      config.layout.xaxis = { 
        title: { text: columns[0], font: { family: 'Microsoft YaHei' } }
      };
      config.layout.yaxis = { 
        title: { text: columns[1], font: { family: 'Microsoft YaHei' } }
      };
      break;

    case 'bar':
      config.data = [{
        x: data.map(row => row[columns[0]]),
        y: data.map(row => row[columns[1]]),
        type: 'bar',
        name: '数量统计'
      }];
      config.layout.xaxis = { 
        title: { text: columns[0], font: { family: 'Microsoft YaHei' } }
      };
      config.layout.yaxis = { 
        title: { text: columns[1], font: { family: 'Microsoft YaHei' } }
      };
      break;

    case 'pie':
      config.data = [{
        values: data.map(row => row[columns[1]]),
        labels: data.map(row => row[columns[0]]),
        type: 'pie',
        name: '占比分布'
      }];
      break;

    case 'scatter':
      config.data = [{
        x: data.map(row => row[columns[0]]),
        y: data.map(row => row[columns[1]]),
        mode: 'markers',
        type: 'scatter',
        name: '数据分布'
      }];
      config.layout.xaxis = { 
        title: { text: columns[0], font: { family: 'Microsoft YaHei' } }
      };
      config.layout.yaxis = { 
        title: { text: columns[1], font: { family: 'Microsoft YaHei' } }
      };
      break;

    case 'histogram':
      config.data = [{
        x: data.map(row => row[columns[0]]),
        type: 'histogram',
        name: '频率分布'
      }];
      config.layout.xaxis = { 
        title: { text: columns[0], font: { family: 'Microsoft YaHei' } }
      };
      config.layout.yaxis = { 
        title: { text: '频次', font: { family: 'Microsoft YaHei' } }
      };
      break;

    default:
      config.data = [{
        type: 'table',
        header: {
          values: columns.map(col => `<b>${col}</b>`),
          align: 'center',
          line: { width: 1, color: '#506784' },
          fill: { color: '#119DFF' },
          font: { family: 'Microsoft YaHei', color: 'white' }
        },
        cells: {
          values: columns.map(col => data.map(row => row[col])),
          align: 'center',
          line: { width: 1, color: '#506784' },
          font: { family: 'Microsoft YaHei' }
        }
      }];
      break;
  }

  return config;
};