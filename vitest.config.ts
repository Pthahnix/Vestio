import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['.test/collectors/**/*.test.ts'],
    globals: true,
  },
});
