import { defineConfig } from "@apps-in-toss/web-framework/config";

export default defineConfig({
  appName: "random-noel-spot",
  brand: { primaryColor: "#F46961" },
  webView: {},
  permissions: [{ name: "geolocation", access: "access" }],
  webBundleDir: "dist",
});
