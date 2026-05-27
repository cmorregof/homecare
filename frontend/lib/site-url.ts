export function getSiteUrl() {
  const configuredUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configuredUrl) {
    return normalizeOrigin(configuredUrl);
  }

  if (typeof window !== "undefined") {
    return window.location.origin;
  }

  const vercelUrl = process.env.VERCEL_URL?.trim();
  if (vercelUrl) {
    return normalizeOrigin(`https://${vercelUrl}`);
  }

  return "http://localhost:3000";
}

export function getAuthCallbackUrl() {
  return `${getSiteUrl()}/auth/callback`;
}

function normalizeOrigin(value: string) {
  try {
    return new URL(value).origin;
  } catch {
    return value.replace(/\/$/, "");
  }
}
