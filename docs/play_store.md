# Publicar CARMEN en Google Play

Apuntado para después de la entrega. No hace falta nada de esto para la
sustentación: la APK de `mobile/` ya se instala y funciona.

Este documento existe porque la pregunta se hizo y la respuesta corta —«no es
duro, es lento, y tal como está hoy la rechazarían»— necesita el detalle de por
qué.

## Por qué la rechazarían hoy

La APK actual es un WebView que abre `homecare-bice-beta.vercel.app`. Google
rechaza explícitamente las aplicaciones que envuelven una web sin aportar valor
propio, y pide al menos una de estas: notificaciones push, navegación nativa,
soporte sin conexión, o integración con el dispositivo.

No es un tecnicismo esquivable: es exactamente la descripción de lo que
construimos, y lo construimos así a propósito porque era lo que servía para la
entrega.

## Los tres bloqueos

### 1. Doce testers, catorce días

Las cuentas de desarrollador **personales** creadas después del 13 de noviembre
de 2023 deben completar una prueba cerrada con **12 testers activos durante 14
días continuos** antes de poder siquiera solicitar acceso a producción. No son
doce instalaciones sueltas: si el número baja, el contador se resiente.

Las cuentas de **organización están exentas**. Si la universidad o la IPS tiene
una, este bloqueo desaparece entero. **Es la primera pregunta que conviene
hacer**, porque cambia el calendario en dos semanas.

### 2. Funcionalidad mínima

Hay que darle a la aplicación algo que un navegador no dé. La opción que vale la
pena es **notificaciones push**, porque no es un trámite para Google: es una
carencia real del producto.

Hoy una alerta de riesgo viaja por correo (`backend/notifications/email.py:16`)
y por Telegram. Al teléfono del paciente, como notificación, no llega nada. Si
alguien registra una medición crítica a las once de la noche, se entera quien
mire el correo.

### 3. Es una aplicación de salud

Tres requisitos:

- Rellenar el formulario de declaración de apps de salud en Play Console
- Publicar una política de privacidad que describa el tratamiento de datos
  personales y sensibles
- Incluir un descargo claro de que **no es un dispositivo médico y no
  diagnostica, trata, cura ni previene ninguna condición**, recordando consultar
  a un profesional

El tercero no es papeleo. CARMEN calcula riesgo cardiovascular y muestra «RIESGO
ACTUAL» con un porcentaje; ese descargo es la diferencia entre una herramienta de
apoyo y una afirmación clínica.

## El trabajo, en orden de dependencia

### Paso 1 — Firma de release

Prerrequisito de todo lo demás: Play Store no acepta nada firmado con la clave
de depuración.

- Generar un keystore y guardarlo como secreto del repositorio, junto con sus
  contraseñas. **No puede vivir en el repo.**
- Añadir `signingConfigs` a `mobile/android/app/build.gradle`
- Cambiar el workflow a `bundleRelease` (Play Store quiere AAB, no APK)
- Mantener el APK de debug en paralelo: es lo que se reparte por fuera

Perder ese keystore significa no poder volver a actualizar la app publicada
nunca. Conviene guardarlo en dos sitios desde el primer día.

### Paso 2 — Notificaciones push

El trabajo de verdad.

- Proyecto de Firebase y `google-services.json` en el proyecto Android
- Plugin `@capacitor/push-notifications`
- Una tabla o columna donde guardar el token FCM de cada dispositivo por
  paciente. Un paciente puede tener varios dispositivos; el modelo tiene que
  contemplarlo desde el principio.
- En el backend, enviar a FCM donde hoy se envía a Resend y a Telegram. El sitio
  natural es junto a `send_risk_email_alert`, que ya recibe el payload completo.
- Decidir **qué** se notifica. Notificar toda medición es ruido y la gente apaga
  las notificaciones; notificar solo lo crítico puede llegar tarde. Esa decisión
  es clínica, no técnica.

### Paso 3 — Algo sin conexión

Hoy sin señal la app enseña una pantalla que dice que no hay señal. Lo mínimo
razonable: guardar la última medición y el último nivel de riesgo para que la
pantalla tenga algo que mostrar. Suma para la política de funcionalidad mínima y
es sensato de todos modos para pacientes con conexión intermitente.

### Paso 4 — Descargo y política de privacidad

- Descargo visible dentro de la aplicación, no enterrado en un menú
- Política de privacidad publicada en una URL estable, enlazada desde la ficha
  de Play Store y desde la propia app
- Formulario de declaración de apps de salud

### Paso 5 — La prueba cerrada

Si la cuenta es personal: reclutar 12 testers y sostenerlos 14 días. Conviene
que sean personas que vayan a abrir la app de verdad, porque además sirve para
encontrar problemas.

## Lo que hay que decidir, y no es técnico

1. **¿Hay cuenta de organización disponible?** Ahorra dos semanas y el
   reclutamiento entero.
2. **¿Qué se notifica y con qué urgencia?** Ver paso 2.
3. **¿Qué dice exactamente el descargo?** Alguien con criterio clínico debería
   redactarlo, no un desarrollador.
4. **¿Hay implicaciones regulatorias más allá de Play Store?** Una aplicación que
   estratifica riesgo cardiovascular para pacientes reales puede estar sujeta a
   normativa sanitaria local. No lo sé y no debería suponerlo: hay que
   preguntarlo antes de publicar, no después.

## Calendario realista

Los 14 días de prueba cerrada no se pueden comprimir, y corren **después** de
tener una build subible. Sumando el desarrollo de push y la revisión de Google,
mes y medio es el suelo, no la estimación.

## Una nota aparte

Si esto avanza hacia pacientes reales, hay un asunto pendiente que deja de ser
menor: una frecuencia cardíaca de 120 lpm aislada produce hoy «riesgo bajo»
(`backend/utils/risk_levels.py:164` le da 2 puntos, y hacen falta 3 para
«moderado»), y se ha visto mostrada con una probabilidad del 100%, que el
fallback de reglas no puede producir porque topa en 95% (`:212`) — sale del
modelo.

Un número así, enseñado a un paciente sin matices, es una afirmación de certeza
que ningún modelo clínico debería hacer. Conviene resolverlo antes de que la
aplicación llegue a más manos, no después.
