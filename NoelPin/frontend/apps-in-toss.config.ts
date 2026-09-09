import { defineConfig } from "@apps-in-toss/web-framework/config";

export default defineConfig({
  appName: "noel-pin",
  brand: {
    primaryColor: "#FF7657",
  },
  webView: {},
  permissions: [
    {
      name: "geolocation",
      access: "access",
    },
  ],
  webBundleDir: "dist",
});
