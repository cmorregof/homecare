# Canal WhatsApp de Carmen — diseño, estado y runbook

Estado al 9 de septiembre de 2026: **código en la rama `feat/whatsapp-channel`, sin
desplegar y sin migración aplicada.** Telegram sigue exactamente igual en producción.

## 1. Qué es y qué no es

WhatsApp es el **segundo canal** de Carmen, no una copia ni un "2.0". El cerebro es uno
solo: validadores deterministas, overrides duros, pipeline LangGraph (ML + Forecast +
agente médico + alertas) y voz. El canal es la boca y los oídos, exactamente la capa que
la tesis del proyecto declara intercambiable.

Motivación: en el piloto (Caldas; el proyecto cubre también Atlántico) "sin app"
significa en la práctica WhatsApp. Telegram es una barrera de adopción real.

## 2. Garantías de no regresión para Telegram

- **Nada de `bot/` cambia.** `handlers.py`, `telegram_bot.py`, `keyboards.py`,
  `validators.py` e `i18n.py` están intactos; el canal WhatsApp los importa, no los edita.
- **Rutas nuevas, aisladas.** `/whatsapp/webhook` responde 503 si faltan las variables
  `WHATSAPP_*`. El servicio se importa de forma perezosa dentro de la ruta: si el canal
  fallara al importar, solo se cae esa ruta.
- **Cambios en archivos compartidos, todos aditivos:**
  - `config.py`: cinco variables opcionales `WHATSAPP_*`.
  - `main.py`: una línea de import y una de `include_router`.
  - `db/repository.py`: dos métodos nuevos (`find_profile_by_whatsapp_phone`,
    `link_whatsapp_account`) y `create_patient_account` acepta `whatsapp_phone`
    (`telegram_chat_id` pasa a opcional con el mismo comportamiento para Telegram).
  - `agents/state.py`: se declara la clave `source` del estado. **Hallazgo latente:**
    LangGraph descarta las claves no declaradas, así que hasta hoy todo signo vital se
    guardaba con `source='telegram'` aunque viniera de otro canal. Para Telegram no
    cambia nada (sigue enviando `telegram`).
- **La suite completa corre en verde** con los tests nuevos incluidos
  (`tests/test_whatsapp_channel.py`, sin red ni Supabase ni OpenAI).
- **Ningún push a `main` hasta después de la presentación.** Railway despliega `main`.

## 3. Arquitectura

```
Meta Cloud API ──POST /whatsapp/webhook──▶ api/routes/whatsapp.py
                                            │ firma X-Hub-Signature-256, 200 inmediato
                                            ▼
                                   channels/whatsapp/service.py
                                   dedup por wamid · sesión por número · BackgroundTasks
                                            ▼
                                   channels/whatsapp/conversation.py
                                   comandos/botones · vinculación · registro · texto libre
                                            │
                    ┌───────────────────────┼────────────────────────┐
                    ▼                       ▼                        ▼
          channels/intake.py      bot/handlers.py (puras)     NurseAgent.process_vital_report
          intake de 11 campos     documento, nombre, estado,  (source="whatsapp")
          (motor sin canal)       historial, texto libre,     validate → save → ML+overrides →
                                  médico asignado             forecast → doctor → alertas → voz
                                            ▼
                                   channels/whatsapp/client.py ──▶ graph.facebook.com
                                   texto, botones de respuesta, marcar leído
```

Archivos:

| Archivo | Qué hace |
|---|---|
| `backend/channels/messages.py` | `Outbound(text, buttons)`: mensaje hacia el paciente sin canal |
| `backend/channels/intake.py` | Motor de intake guiado (11 pasos) como máquina de estados pura; mismos validadores, mismas preguntas, mismos avisos deterministas de FR y SpO2 que Telegram |
| `backend/channels/whatsapp/webhook.py` | Parseo del payload de Meta (texto, botones, no soportados; ignora `statuses`) y verificación HMAC |
| `backend/channels/whatsapp/client.py` | Envío por Graph API con reintentos; límites de WhatsApp (4096 caracteres, 3 botones, títulos de 20) |
| `backend/channels/whatsapp/session.py` | Sesión por número (idioma, perfil, borrador, banderas); en memoria; TTL del intake 2 h |
| `backend/channels/whatsapp/conversation.py` | La conversación completa; catálogo `WHATSAPP_MESSAGES` solo para textos propios del canal |
| `backend/channels/whatsapp/service.py` | Dedup, lock por número, manejo de errores con respuesta segura, singleton configurado desde `settings` |
| `backend/api/routes/whatsapp.py` | `GET` verificación (`hub.challenge`) y `POST` mensajes |
| `backend/db/migrations/20260909_add_whatsapp_channel.sql` | `profiles.whatsapp_phone` + `vital_signs.source` acepta `'whatsapp'` |

Comportamiento que se conserva de Telegram: emergencias en texto libre son
deterministas y nunca pasan por el LLM; los avisos de seguridad dentro del intake
tampoco; el clínico decide; ante cualquier fallo del pipeline el paciente recibe un
mensaje seguro con el 123 y el error queda en logs.

Diferencias propias del canal:

- Sin menú de comandos: se aceptan `/vitales` y palabras exactas (`vitales`, `estado`,
  `historial`, `ayuda`, `emergencia`, `idioma`, `cancelar`) y botones de respuesta.
- La frase de emergencia lleva un botón "🚨 Avisar al equipo" en lugar de pedir
  `/emergencia`.
- Idioma: elección explícita > `profiles.language` > español. WhatsApp no manda el
  idioma del teléfono.
- Identidad por número (`wa_id`, E.164 sin `+`). La vinculación sigue siendo por documento.

## 4. Configuración en Meta (lo que hace Carlos)

1. En [developers.facebook.com](https://developers.facebook.com) crear una app de tipo
   **Business** y añadir el producto **WhatsApp**. Meta entrega un **número de prueba**
   gratuito con hasta 5 destinatarios de prueba.
2. En *WhatsApp → API Setup* anotar el **Phone number ID** y generar un **access token**
   (el temporal dura 24 h; para algo estable, crear un *System User* en Business
   Settings y un token permanente con permiso `whatsapp_business_messaging`).
3. Añadir tu propio celular como destinatario de prueba (llega un código por WhatsApp).
4. En *App Settings → Basic* copiar el **App Secret** (firma del webhook).
5. Elegir un **verify token** cualquiera (una cadena aleatoria larga).
6. Registrar el webhook (paso 6 del runbook local) y suscribirse al campo **messages**.

Variables resultantes (van en el entorno local, **no en Railway hoy**):

```
WHATSAPP_ACCESS_TOKEN=EAAG...
WHATSAPP_PHONE_NUMBER_ID=1065...
WHATSAPP_VERIFY_TOKEN=<cadena aleatoria elegida>
WHATSAPP_APP_SECRET=<App Secret de la app>
WHATSAPP_API_VERSION=v25.0
```

Versión de Graph API: la última es v26.0 (29 de julio de 2026); v25.0 está soportada
hasta julio de 2028 y es la que usan los ejemplos de la documentación de mensajes.

## 5. Prueba local sin tocar producción

Producción no cambia porque: el webhook de Telegram no se reconfigura al arrancar
(`main.py` no llama a `configure_webhook`), no se hace push a `main`, y el webhook de
WhatsApp apunta a un túnel local.

Lo que sí es real aunque corras en local: Supabase, OpenAI y las alertas por Telegram y
correo a los médicos usan las credenciales de `backend/.env`. **Primer test con signos
normales**, y si es posible, después de la presentación.

```bash
cd backend && PYTHONPATH=. WHATSAPP_ACCESS_TOKEN=... WHATSAPP_PHONE_NUMBER_ID=... WHATSAPP_VERIFY_TOKEN=... WHATSAPP_APP_SECRET=... ../.venv/bin/python -m uvicorn main:app --port 8000
```

En otra terminal, un túnel HTTPS (cualquiera de los dos):

```bash
brew install cloudflared && cloudflared tunnel --url http://localhost:8000
```

```bash
ngrok http 8000
```

Registrar en Meta (*WhatsApp → Configuration → Webhook*): URL
`https://<túnel>/whatsapp/webhook` y el verify token. Meta hace un `GET` con
`hub.challenge`; el backend responde el challenge si el token coincide.

Antes del primer reporte real por WhatsApp, aplicar la migración en Supabase
(SQL Editor): `backend/db/migrations/20260909_add_whatsapp_channel.sql`. Es aditiva e
idempotente. Sin ella: el vínculo documento↔número queda solo en memoria (WARNING en
logs) y el INSERT en `vital_signs` con `source='whatsapp'` falla; el paciente recibe el
mensaje seguro de "no pude procesar tu reporte".

## 6. Restricciones de WhatsApp que cambian el diseño

- **Ventana de 24 horas.** Carmen solo puede escribir libremente dentro de las 24 h
  siguientes al último mensaje del paciente. Fuera de ella, cualquier mensaje iniciado
  por el sistema debe ser una **plantilla** aprobada por Meta (categoría *utility*).
  Afecta a los recordatorios de un paciente que lleva un día sin reportar y a cualquier
  aviso proactivo. La respuesta al reporte y la alerta al paciente caen dentro de la
  ventana.
- **Cuenta y política.** Número no vinculado a un WhatsApp personal, verificación de
  negocio en Meta para salir del modo de prueba, y revisar la *Business Messaging
  Policy* para uso en salud. Precio por conversación o por plantilla según la tarifa
  vigente para Colombia. Telegram es gratis.
- **Datos.** El teléfono es un dato personal más sensible que un id de chat: el
  consentimiento de Habeas Data del piloto debe cubrirlo.
- **Staging.** Probar plantillas contra el número de producción dispara mensajes reales.
  El canal hace inevitable el paso 3 del roadmap.

## 7. Pendientes (en orden)

1. **Prueba de extremo a extremo** con el número de prueba de Meta y un paciente con
   signos normales. Aplicar la migración antes.
2. **Alerta al paciente por WhatsApp.** Hoy `NurseAgent.send_alerts` avisa al paciente
   solo por Telegram (`patient_telegram_chat_id`); el paciente de WhatsApp recibe el
   riesgo en la respuesta del reporte, no como mensaje separado. Requiere enrutar por
   canal en `send_alerts` y ampliar `get_alert_recipients` con `patient_whatsapp_phone`.
   Se hace después de la presentación porque toca `nurse_agent.py`.
3. **Recordatorios cada 6 h** para pacientes de WhatsApp: plantilla aprobada + job en
   el scheduler (`send_monitoring_reminders` hoy es solo Telegram).
4. **Sesiones persistidas** en Supabase detrás de `SessionStore` (hoy en memoria; un
   redeploy borra los intakes a medias, igual que en Telegram).
5. **Migrar Telegram al motor común** `channels/intake.py` para que haya un solo
   intake. Los tests existentes son la red de seguridad.
6. Reconocer pacientes ya registrados por la IPS por su `profiles.phone` normalizado,
   para que no tengan que escribir el documento.
7. Notas de voz: transcripción antes del extractor (hoy se responde "solo texto").
8. Staging: segundo bot, segundo número, segunda base.
