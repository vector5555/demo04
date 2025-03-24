<template>
  <div id="app">
    <query-result 
      :original-sql="currentSQL" 
      @update:results="handleQueryResults">
    </query-result>
  </div>
</template>

<script>
import QueryResult from './components/QueryResult.vue'

export default {
  name: 'App',
  components: {
    QueryResult
  },
  data() {
    return {
      currentSQL: '',
      results: []
    }
  },
  methods: {
    updateResults(newResults) {
      this.results = newResults
    }
  }
}
</script>