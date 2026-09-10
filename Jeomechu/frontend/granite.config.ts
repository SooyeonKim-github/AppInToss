import { defineConfig } from "@apps-in-toss/web-framework/config";

export default defineConfig({
  appName: "jeomechu",
  brand: {
    displayName: "김대리의 저메추",
    primaryColor: "#FF6B4A",
    // 앱인토스 콘솔에 로고를 업로드한 뒤 같은 이미지 URL로 교체한다.
    icon: "",
  },
  web: {
    host: "localhost",
    port: 5173,
    commands: {
      dev: "vite dev",
      build: "vite build",
    },
  },
  permissions: [],
  outdir: "dist",
  webViewProps: {
    type: "partner",
  },
});
