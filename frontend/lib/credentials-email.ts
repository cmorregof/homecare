import { BRAND_NAME } from "@/lib/brand";

const RESEND_ENDPOINT = "https://api.resend.com/emails";

/**
 * Sends a new user their credentials, once.
 *
 * This is the only moment the password can be sent at all: Supabase stores a
 * bcrypt hash, so nobody — not an administrator, not this code — can read it
 * back later. "Que sepan cuáles son por si se les pierden" is therefore served
 * by this message and by a password reset, not by looking the password up.
 *
 * It posts to Resend directly, matching backend/notifications/email.py:13
 * rather than adding a mail library. A failure is reported to the caller and
 * never throws: the account exists by this point, and losing it because an
 * email bounced would be worse than an administrator reading the password off
 * the screen.
 */
export async function sendCredentialsEmail(params: {
  to: string;
  fullName: string;
  password: string;
  loginUrl: string;
}): Promise<{ sent: boolean; reason?: string }> {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.FROM_EMAIL;
  if (!apiKey || !from) {
    return { sent: false, reason: "RESEND_API_KEY o FROM_EMAIL no están configurados." };
  }

  try {
    const response = await fetch(RESEND_ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from,
        to: [params.to],
        subject: `Tu cuenta de ${BRAND_NAME}`,
        html: buildCredentialsHtml(params),
      }),
    });
    if (!response.ok) {
      return { sent: false, reason: `Resend respondió ${response.status}.` };
    }
    return { sent: true };
  } catch {
    return { sent: false, reason: "No se pudo contactar al servicio de correo." };
  }
}

function buildCredentialsHtml({
  fullName,
  to,
  password,
  loginUrl,
}: {
  fullName: string;
  to: string;
  password: string;
  loginUrl: string;
}) {
  return `
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #17202a;">
        <h2>Bienvenido a ${escapeHtml(BRAND_NAME)}</h2>
        <p>Hola ${escapeHtml(fullName)}, ya tienes una cuenta creada.</p>
        <p>
          <strong>Correo:</strong> ${escapeHtml(to)}<br />
          <strong>Contraseña temporal:</strong>
          <code style="font-size: 16px;">${escapeHtml(password)}</code>
        </p>
        <p><a href="${escapeHtml(loginUrl)}">Entrar a ${escapeHtml(BRAND_NAME)}</a></p>
        <p>
          Cambia la contraseña la primera vez que entres. Este es el único mensaje que la
          contiene: no se guarda en ninguna parte legible, así que si la pierdes habrá que
          restablecerla, no consultarla.
        </p>
        <p style="color: #5b6b7c; font-size: 13px;">
          Si no esperabas esta cuenta, avisa al equipo de ${escapeHtml(BRAND_NAME)} y no uses el enlace.
        </p>
      </body>
    </html>
  `;
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
