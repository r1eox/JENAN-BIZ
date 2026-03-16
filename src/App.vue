<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { refreshProfile, isLoggedIn } from './stores/authStore'

onMounted(async () => {
  if (isLoggedIn.value) {
    await refreshProfile()
  }
})
</script>
