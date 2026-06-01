// =====================================================================
// vite.config.ts
// 역할: Vite 빌드 도구 설정
// - figmaAssetResolver: Figma 에셋 경로 처리 (기존 유지)
// - resolve.alias: @ → src/ 경로 별칭 (기존 유지)
// - server.proxy: 개발 환경에서 /api 요청을 FastAPI 로 프록시
//   프록시 사용 시 src/api/client.ts 의 BASE_URL 을 "" 로 변경하세요
// =====================================================================

import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'


function figmaAssetResolver() {
  return {
    name: 'figma-asset-resolver',
    resolveId(id) {
      if (id.startsWith('figma:asset/')) {
        const filename = id.replace('figma:asset/', '')
        return path.resolve(__dirname, 'src/assets', filename)
      }
    },
  }
}

export default defineConfig({
  plugins: [
    figmaAssetResolver(),
    // The React and Tailwind plugins are both required for Make, even if
    // Tailwind is not being actively used – do not remove them
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': path.resolve(__dirname, './src'),
    },
  },

  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],

  server: {
    // 개발 환경 API 프록시 설정
    // - /api/** 요청을 FastAPI 서버(http://localhost:8000)로 전달
    // - 이 설정을 사용하면 CORS 없이 /api/... 로 직접 요청 가능
    // - TODO: 실제 사용 시 client.ts 의 BASE_URL 을 "" 로 변경하거나
    //         VITE_API_BASE_URL 환경변수를 제거하면 됨
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
