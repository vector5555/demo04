import React from 'react';
import { Input } from 'antd';

const { Search } = Input;

function QueryInput({ loading, onSearch }) {
  return (
    <div className="input-container">
      <Search
        placeholder="请输入自然语言查询，例如：查询所有监测站点的数据"
        enterButton="发送"
        size="large"
        loading={loading}
        onSearch={onSearch}
      />
    </div>
  );
}

export default QueryInput;