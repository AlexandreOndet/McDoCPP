import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [
    sveltekit({
      adapter: adapter({ pages: 'build', assets: 'build', strict: true }),
      prerender: { handleHttpError: 'warn' },
      alias: { '$lib': 'src/lib' }
    })
  ],
  test: { include: ['tests/**/*.test.ts'], environment: 'node' }
});
