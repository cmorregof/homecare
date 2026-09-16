# CARMEN para Android

APK instalable que abre la aplicación web de CARMEN dentro de una ventana
nativa. No es una aplicación aparte: es la misma que está en producción, con su
propio icono en el cajón de aplicaciones.

## Cómo conseguir la APK

Enlace directo, que se puede abrir desde el propio teléfono:

**https://github.com/cmorregof/homecare/releases/download/android-latest/CARMEN.apk**

Descarga el `.apk` sin pasar por la interfaz de Actions y sin iniciar sesión en
GitHub. La dirección no cambia: cada build sobre `main` reemplaza el fichero en
esa misma release, así que un enlace ya compartido sigue sirviendo.

Al abrirla, Android pide permitir **instalar aplicaciones de orígenes
desconocidos**. Es normal: la aplicación no viene de Play Store.

Para una build de una rama, que no toca la release: pestaña **Actions** →
workflow **Android APK** → la ejecución → **Artifacts** → **CARMEN**. Eso sí
baja un zip y requiere sesión iniciada.

## Qué es y qué no es

La APK **no contiene el producto**. Contiene la dirección del producto. Al
abrirla carga `https://homecare-bice-beta.vercel.app`, definida en
`capacitor.config.js`.

Eso tiene tres consecuencias que conviene entender antes de repartirla:

- **Se actualiza sola.** Un arreglo desplegado en Vercel llega a todos los
  teléfonos en cuanto lo recargan. No hay que recompilar ni volver a repartir
  nada, salvo que cambie la carcasa misma.
- **Necesita internet siempre.** Sin conexión muestra `www/index.html`, que solo
  dice que no hay señal. No hay modo sin conexión ni datos guardados en el
  teléfono.
- **Es la web.** Se siente como la web, porque lo es. No hay notificaciones
  push, ni cámara, ni acceso a sensores. Si algún día hacen falta, hay que
  añadir plugins de Capacitor, y eso ya es otro trabajo.

Se eligió así a sabiendas. La aplicación web está renderizada en el servidor: el
middleware protege cada ruta por rol, las pantallas de administración leen
Supabase desde el servidor, y la creación de usuarios corre en un route handler
que tiene la clave de servicio. Nada de eso puede exportarse a un paquete
estático dentro de una APK.

### Por qué no se reutilizó la app de Expo

En `joamontesgi/proyecto_daniela` hay una `salud-cardiaca-app` hecha con Expo,
con sus pantallas completas. No sirve tal cual: apunta a
`http://10.137.208.154:8000` —una IP de red local, fija en el código, contra un
servidor de desarrollo de Laravel— y llama a `/api/login`, `/api/register` y
`/api/risk-measurements`, que no existen en el backend de CARMEN. Compilarla
daría una aplicación que abre y falla al primer toque.

Convertirla es un proyecto aparte: habría que reescribir la autenticación a
Supabase y toda la capa de datos a las tablas de CARMEN.

## Cambiar la dirección a la que apunta

En `capacitor.config.js`, `server.url` y `server.allowNavigation`. **Las dos**:
`allowNavigation` es lo que decide qué se abre dentro de la carcasa y qué se
entrega al sistema. Si se cambia solo `url`, el sitio se abriría fuera, en el
navegador.

Después: `npm run sync`, y vuelve a compilar.

## Trabajar en local

Solo hace falta si se toca la carcasa. Requiere Android Studio o el SDK.

```bash
cd mobile
npm install
npx cap sync android
cd android && ./gradlew assembleDebug
```

La APK sale en `android/app/build/outputs/apk/debug/app-debug.apk`. El
workflow la renombra a `CARMEN.apk` antes de publicarla; en local no.

## Detalles que ya están resueltos

- **Botón atrás.** Capacitor 6.2.2 no lo gestiona, así que por defecto cierra la
  aplicación desde cualquier pantalla. `MainActivity.java` registra un callback
  en el dispatcher para que navegue hacia atrás en el historial y solo salga
  cuando ya no queda nada.
- **Enlaces externos.** El enlace de Telegram del panel del paciente, o el de un
  correo de confirmación, se entregan al sistema en lugar de abrirse dentro de
  una ventana sin barra de direcciones ni forma de volver.
- **Iconos.** Generados desde `frontend/app/icon.png` en las cinco densidades,
  incluido el icono adaptativo con el logo dentro de la zona segura de 66dp para
  que el recorte del lanzador no se lo coma.

## Antes de publicarla en Play Store

El plan completo, con los tres bloqueos reales y lo que hay que decidir antes de
intentarlo, está en [docs/play_store.md](../docs/play_store.md). Resumen: tal
como está hoy la rechazarían, porque un WebView que envuelve una web sin aportar
valor propio no pasa la política de funcionalidad mínima.

## Firma de release y App Bundle

La APK del enlace sigue firmada con la clave de depuración: sirve para instalar
a mano y no cambia. En paralelo, el mismo workflow compila
`bundleRelease`, el App Bundle (`.aab`) que Play Store exige, y lo firma con
un keystore de subida que **no vive en el repositorio**: `app/build.gradle`
lo lee de la variable `CARMEN_KEYSTORE_PATH`, y el workflow la rellena
decodificando el secreto. Si el secreto no existe, el bundle sale sin firmar y
no se publica; la APK de debug no se ve afectada.

El `versionCode` del bundle es el número de ejecución del workflow, porque
Play Console rechaza subir un código que no sea mayor que el anterior.

### Generar el keystore (una sola vez, una persona)

```bash
keytool -genkeypair -v -keystore carmen-upload.jks -alias carmen \
  -keyalg RSA -keysize 2048 -validity 10000
```

Guárdalo en **dos sitios** fuera del repositorio. Perderlo significa no poder
actualizar nunca más la app publicada. Después, cuatro secretos del
repositorio (Settings → Secrets and variables → Actions):

| Secreto | Valor |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | `base64 -i carmen-upload.jks` (una sola línea) |
| `ANDROID_KEYSTORE_PASSWORD` | contraseña del keystore |
| `ANDROID_KEY_ALIAS` | `carmen` |
| `ANDROID_KEY_PASSWORD` | contraseña de la clave |

El bundle firmado queda en el artifact **CARMEN-aab** de la ejecución del
workflow; ese es el fichero que se sube a Play Console. El `applicationId`
`co.homecareccv.carmen` no se puede cambiar a partir de la primera
publicación.
