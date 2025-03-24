// 修改请求 URL
async submitQuery() {
    try {
        const response = await fetch('http://localhost:8000/query_nl', {  // 从 /query 改为 /query_nl
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query_text: this.queryText,
                context_id: null
            })
        });
        const result = await response.json();
        this.$emit('query-result', result);
    } catch (error) {
        console.error('查询失败:', error);
    }
}