# AHA/ASA 2021 — Prevención secundaria de ACV: ficha de referencia (SIN texto completo)

> **ADVERTENCIA: este archivo NO contiene las recomendaciones de la guía.**
> Es una ficha bibliográfica. Ninguna cifra, umbral ni recomendación de la guía AHA/ASA
> está reproducida aquí, porque el texto completo es de acceso restringido y las páginas
> públicas de la AHA llevan el aviso «All rights reserved. Unauthorized use prohibited.»
>
> Si una consulta del RAG cae en este documento, la respuesta correcta es **remitir a la
> fuente**, no responder con contenido de la guía.

- **Tipo de documento:** ficha de procedencia redactada por el asistente. No es un extracto.
- **Contenido clínico literal:** ninguno.
- **Fecha:** 2026-08-27

---

## Cita

Kleindorfer DO, Towfighi A, Chaturvedi S, Cockroft KM, Gutierrez J, Lombardi-Hill D,
Kamel H, Kernan WN, Kittner SJ, Leira EC, Lennon O, Meschia JF, Nguyen TN, Pollak PM,
Santangeli P, Sharrief AZ, Smith SC, Turan TN, Williams LS.
**2021 Guideline for the Prevention of Stroke in Patients With Stroke and Transient
Ischemic Attack: A Guideline From the American Heart Association/American Stroke
Association.** *Stroke.* 2021;52(7):e364–e467.

- **DOI:** 10.1161/STR.0000000000000375
- **PMID:** 34024117
- **Corrección publicada:** PubMed lista «Correction to: 2021 Guideline for the Prevention
  of Stroke…», PMID 34181456. *No se pudo abrir el registro para verificar volumen y
  páginas de la corrección* (ver Estado de acceso). Quien cite la guía debe revisarla.

## Por qué esta guía y no la de 2024

La guía AHA/ASA de **2024** es de prevención **primaria** de ACV
(*2024 Guideline for the Primary Prevention of Stroke*, DOI 10.1161/STR.0000000000000475).
La de prevención **secundaria** — pacientes que ya tuvieron ACV o AIT — es la de **2021**,
la citada arriba. Para HomecareCCV la pertinente es esta: sus pacientes ya tuvieron el
evento.

## Estado de acceso (verificado el 2026-08-27)

| Recurso | Estado |
|---|---|
| Texto completo en `ahajournals.org` | Restringido. Sin PDF abierto. El servidor responde **403** a cualquier cliente automatizado. |
| Resumen público en `professional.heart.org` | Accesible en navegador. Son 3 puntos descriptivos de las secciones de la guía: **no contienen umbrales ni recomendaciones**. Pie de página: «©2026 American Heart Association, Inc. All rights reserved. Unauthorized use prohibited.» |
| Ficha de PubMed | Accesible en navegador. Bloqueada por reCAPTCHA para clientes automatizados. |
| Hub de la guía en `professional.heart.org` | Ofrece una serie de diapositivas clínicas en PPTX. Material de la AHA, mismas condiciones. |
| PubMed Central | La guía **no** está depositada. |

**Enlaces:**

- Texto completo (restringido): https://www.ahajournals.org/doi/10.1161/STR.0000000000000375
- Hub de la guía: https://professional.heart.org/en/guidelines-statements/2021-guideline-for-the-prevention-of-stroke-in-patients-with-stroke-andstr0000000000000375
- Resumen público: https://professional.heart.org/en/science-news/2021-guideline-for-the-prevention-of-stroke-in-patients-with-stroke-and-transient-ischemic-attack
- PubMed: https://pubmed.ncbi.nlm.nih.gov/34024117/

## Por qué no se incorporó un resumen

Tres razones, en orden de peso:

1. **Riesgo clínico.** Un documento corto que *parezca* la guía AHA pero que en realidad
   sea una descripción de sus secciones es peor que no tener nada en un sistema que decide
   escalamientos. El RAG lo recuperaría con la etiqueta «AHA/ASA prevención secundaria» y
   respondería con material que no contiene ninguna recomendación.
2. **Condiciones de uso.** La página pública declara «Unauthorized use prohibited». Incluir
   su texto en una base redistribuible es una decisión que corresponde al titular del
   proyecto, no al asistente, y conviene tomarla explícitamente.
3. **Valor nulo.** El resumen público no tiene umbrales, clases de recomendación ni niveles
   de evidencia. No aporta nada que el motor de alertas pueda usar.

## Qué cubre la base mientras tanto

La prevención secundaria cardio-cerebrovascular queda cubierta por fuentes que sí están
completas y son citables:

| Tema | Archivo en esta base |
|---|---|
| ACV isquémico: sospecha, escalas, traslado y ventana terapéutica | `minsalud_gpc_acv_isquemico_2015_recomendaciones.md` |
| Tamizaje de ACV fuera del hospital (LAPSS) y NIHSS | `minsalud_gpc_acv_isquemico_2015_escalas_prehospitalarias_nihss.md` |
| Control de presión arterial, metas y seguimiento | `minsalud_gpc_hta_2025_recomendaciones_tratamiento_seguimiento.md` |
| Umbrales de PA y equivalencias AMPA/MAPA para toma domiciliaria | `minsalud_gpc_hta_2025_clasificacion_umbrales_ampa.md` |
| Riesgo cardiovascular y metas lipídicas | `minsalud_gpc_dislipidemias_2014_riesgo_cv_framingham_colombia.md` |
| Detección de deterioro y escalamiento | `rcp_news2_tabla_puntuacion_y_umbrales.md`, `mews_tabla_puntuacion_ccby.md` |

## Cómo completar esta ficha si se consigue acceso

Con acceso institucional a *Stroke*, descargar el PDF a
`backend/rag/documents/_originales/` con el nombre
`aha_asa_2021_prevencion_secundaria_acv.pdf`, y añadir al spec
`scripts/rag_extracts_spec.json` una entrada con los rangos de página de las tablas de
recomendaciones (Clase de recomendación y Nivel de evidencia). El pipeline hace el resto:
`--dump`, `--build`, y `build_sources_md.py`.

Aun con acceso, **el uso permitido depende de la licencia institucional**: sirve para
consulta interna del equipo, no necesariamente para redistribuir el texto.
