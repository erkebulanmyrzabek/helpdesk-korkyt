<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const timeString = ref('')
let intervalId = null

const updateTime = () => {
    const now = new Date()
    timeString.value = new Intl.DateTimeFormat('ru-RU', {
        timeZone: 'Asia/Almaty',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    }).format(now)
}

onMounted(() => {
    updateTime()
    intervalId = setInterval(updateTime, 1000)
})

onUnmounted(() => {
    if (intervalId) clearInterval(intervalId)
})
</script>

<template>
    <div class="clock-container">
        <i class="bi bi-clock me-2"></i>
        <span class="fw-bold">{{ timeString }}</span>
        <span class="ms-2 small text-muted">(Asia/Almaty)</span>
    </div>
</template>

<style scoped>
.clock-container {
    font-family: 'Courier New', Courier, monospace;
    font-size: 1.2rem;
    color: #0d6efd;
    background: #f8f9fa;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    display: inline-flex;
    align-items: center;
}
</style>
