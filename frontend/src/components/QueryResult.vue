<template>
    <div class="query-result">
        <div class="sql-editor-container">
            <textarea v-model="editedSQL" class="sql-editor" placeholder="编辑SQL语句"></textarea>
            <button @click="executeEditedSQL" class="execute-btn">执行编辑后的SQL</button>
        </div>
        <div class="results-container" v-if="queryResults.length">
            <!-- 显示查询结果 -->
        </div>
    </div>
</template>

<script>
export default {
    props: {
        originalSQL: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            editedSQL: '',
            queryResults: []
        }
    },
    watch: {
        originalSQL: {
            immediate: true,
            handler(newVal) {
                this.editedSQL = newVal;
            }
        }
    },
    methods: {
        async executeEditedSQL() {
            try {
                console.log('执行编辑后的SQL...');
                const response = await fetch('http://localhost:8000/execute_edited', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        original_sql: this.originalSQL,
                        edited_sql: this.editedSQL
                    })
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    this.queryResults = result.data;
                    console.log('SQL执行成功');
                } else {
                    console.error('SQL执行失败:', result.message);
                }
            } catch (error) {
                console.error('执行SQL时出错:', error);
            }
        }
    }
}
</script>

<style scoped>
.query-result {
    padding: 15px;
}

.sql-editor-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 15px;
}

.sql-editor {
    width: 100%;
    min-height: 100px;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.execute-btn {
    padding: 8px 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    align-self: flex-start;
}

.execute-btn:hover {
    background-color: #45a049;
}
</style>