<template>
  <div class="shell">
    <div class="shell__backdrop"></div>
    <main class="shell__content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(84, 156, 255, 0.18), transparent 32%),
    radial-gradient(circle at 85% 20%, rgba(75, 192, 192, 0.18), transparent 28%),
    linear-gradient(180deg, #06111f 0%, #0d1421 100%);
  color: #f5f7fb;
}

.shell__backdrop {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(143, 163, 191, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(143, 163, 191, 0.08) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.5), transparent 88%);
}

.shell__content {
  position: relative;
  max-width: 1320px;
  margin: 0 auto;
  padding: 40px 20px 64px;
}
</style>
