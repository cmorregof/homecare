/**
 * Android shell around the deployed CARMEN web app.
 *
 * `server.url` means the APK carries no copy of the product: it opens the live
 * site. That is deliberate. The web app is server-rendered — middleware guards
 * every role route, the admin screens read Supabase from the server, and user
 * creation runs in a route handler holding the service key — so there is
 * nothing to export into a bundle. Pointing at the deployment also means a fix
 * shipped to Vercel reaches every installed phone without rebuilding or
 * redistributing an APK.
 *
 * The cost is honest and worth stating: no offline mode. Without a connection
 * the app shows www/index.html, not the product.
 *
 * Plain JavaScript rather than TypeScript so the file can carry this comment
 * without pulling a TypeScript install into the module just to read a config.
 *
 * @type {import('@capacitor/cli').CapacitorConfig}
 */
const config = {
  appId: "co.homecareccv.carmen",
  appName: "CARMEN",
  webDir: "www",
  server: {
    url: "https://homecare-bice-beta.vercel.app",
    // Only the product's own origin opens inside the shell. Anything else —
    // the Telegram link on the patient dashboard, a confirmation email link —
    // is handed to the system, so it lands in Telegram or the browser instead
    // of a webview with no address bar and no way back.
    allowNavigation: ["homecare-bice-beta.vercel.app"],
    androidScheme: "https",
  },
  android: {
    // The site is https-only; leaving cleartext off means a misconfigured URL
    // fails loudly instead of silently downgrading.
    allowMixedContent: false,
  },
};

module.exports = config;
