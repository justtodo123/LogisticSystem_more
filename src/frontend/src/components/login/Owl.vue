<script setup lang="ts">
defineProps<{
  closeEyes: boolean
}>()
</script>

<template>
  <div class="owl" :class="{ 'owl-password': closeEyes }">
    <div class="hand-down-left" />
    <div class="hand-down-right" />
    <div class="hand-up-left" />
    <div class="hand-up-right" />
    <div class="close-eyes" />
  </div>
</template>

<style scoped>
.owl {
  position: relative;
  width: 120px;
  height: 95px;
  transform: translateY(12%);
  background-image: url('@/assets/login/face.png');
  background-repeat: no-repeat;
  background-size: 100%;
}

.hand-down-left,
.hand-down-right {
  z-index: 2;
  position: absolute;
  width: 45px;
  height: 25px;
  transition: transform 0.2s linear;
}

.hand-down-left {
  bottom: 3px;
  left: -35px;
  background-image: url('@/assets/login/hand-down-left.png');
  background-repeat: no-repeat;
  background-size: 100%;
}

.hand-down-right {
  bottom: 3px;
  right: -40px;
  background-image: url('@/assets/login/hand-down-right.png');
  background-repeat: no-repeat;
  background-size: 100%;
}

.hand-up-left,
.hand-up-right {
  z-index: 3;
  position: absolute;
  width: 50px;
  height: 40px;
  opacity: 0;
  transition: opacity 0.1s linear 0.1s;
}

.hand-up-left {
  bottom: 11px;
  left: -5px;
  background-image: url('@/assets/login/hand-up-left.png');
  background-repeat: no-repeat;
  background-size: 100%;
}

.hand-up-right {
  bottom: 11px;
  right: 5px;
  background-image: url('@/assets/login/hand-up-right.png');
  background-repeat: no-repeat;
  background-size: 100%;
}

.close-eyes {
  z-index: 1;
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: opacity 0.1s linear 0.1s;
  background-image: url('@/assets/login/close-eyes.png');
  background-repeat: no-repeat;
  background-size: 100%;
}

.owl-password .hand-down-left {
  transform: translateX(30px) scale(0) translateY(-10px);
}

.owl-password .hand-down-right {
  transform: translateX(-40px) scale(0) translateY(-10px);
}

.owl-password .hand-up-left,
.owl-password .hand-up-right,
.owl-password .close-eyes {
  opacity: 1;
}
</style>
