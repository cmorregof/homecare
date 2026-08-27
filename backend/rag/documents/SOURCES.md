# Fuentes de la base RAG clínica — HomecareCCV

**Generado automáticamente por `scripts/build_sources_md.py`.** Las cifras de tamaño y
los SHA256 se leen de `_originales/manifest.tsv` en cada corrida; no se transcriben a mano.

- **Fecha de descarga de los originales:** 2026-08-27
- **Fecha de esta generación:** 2026-08-27

## Cómo se produjo esto

1. `bash scripts/fetch_clinical_guidelines.sh` — descarga los PDF oficiales, verifica que
   cada archivo empiece con `%PDF`, calcula SHA256 y escribe el manifiesto.
2. `python3 scripts/build_rag_extracts.py --dump` — vuelca el texto de cada PDF con
   `pdftotext -layout`. Extracción mecánica: **no hay modelo de lenguaje en el camino.**
3. `python3 scripts/build_rag_extracts.py --build` — arma los `.md` copiando texto literal
   de rangos de página verificados uno a uno contra el volcado, con un encabezado de
   procedencia y corte duro en 50 KB.

Ningún contenido clínico de estos archivos fue redactado, resumido ni parafraseado.
Lo único escrito por el asistente son los encabezados de procedencia y este documento.


---

## Extractos construidos

| Archivo | Tamaño | PDF de origen | Páginas | Secciones extraídas |
|---|---|---|---|---|
| `minsalud_gpc_hta_2025_recomendaciones_prevencion_diagnostico.md` | 41 KB | `minsalud_gpc_hta_2025_guia18_tercera_edicion.pdf` | 49-75 | Seccion 1.4 Listado de recomendaciones, primera mitad: modulos de prevencion, diagnostico, abordaje inicial y dano a organo blanco (pp. 49-75 del PDF) |
| `minsalud_gpc_hta_2025_recomendaciones_tratamiento_seguimiento.md` | 40 KB | `minsalud_gpc_hta_2025_guia18_tercera_edicion.pdf` | 76-103 | Seccion 1.4 Listado de recomendaciones, segunda mitad: estimacion del riesgo cardiovascular, monoterapia vs politerapia, tratamiento no farmacologico, prevencion primaria y seguimiento incluida tecnica de medicion y telemonitoreo (pp. 76-103 del PDF) |
| `minsalud_gpc_hta_2025_clasificacion_umbrales_ampa.md` | 29 KB | `minsalud_gpc_hta_2025_guia18_tercera_edicion.pdf` | 27-30, 56-59, 316-321, 332-333 | Definiciones de AMPA, MAPA, hipertension de bata blanca y enmascarada (pp. 27-30); equivalencia de valores entre consultorio, AMPA y MAPA (pp. 56-59); Tablas 7-2, 7-3 y 7-4 de clasificacion de presion arterial (pp. 316-321); umbral de emergencia hipertensiva 180/110 mmHg (pp. 332-333) |
| `minsalud_gpc_hta_2017_recomendaciones_segunda_edicion.md` | 24 KB | `minsalud_gpc_hta_2017_guia18_segunda_edicion.pdf` | 38-51 | Resumen de recomendaciones completo: prevencion, diagnostico, tratamiento y algoritmo de manejo (pp. 38-51 del PDF) |
| `minsalud_gpc_hta_2013_pacientes_signos_alarma.md` | 16 KB | `minsalud_gpc_hta_2013_pacientes.pdf` | 1-17 | Documento completo (17 pp.): lenguaje dirigido al paciente y signos de alarma |
| `minsalud_gpc_acv_isquemico_2015_recomendaciones.md` | 40 KB | `minsalud_gpc_acv_isquemico_2015_guia54_profesionales.pdf` | 32-57 | Capitulo 14, Resumen de recomendaciones completo (pp. 32-57): sospecha clinica, notificacion y traslado, escalas de severidad, ventana terapeutica y trombolisis |
| `minsalud_gpc_acv_isquemico_2015_escalas_prehospitalarias_nihss.md` | 18 KB | `minsalud_gpc_acv_isquemico_2015_guia54_profesionales.pdf` | 58-69 | 15.2 Escalas de atencion prehospitalaria incluida LAPSS; 15.4 National Institute of Health Stroke Scale (NIHSS) con hoja de registro (pp. 58-69) |
| `minsalud_gpc_dislipidemias_2014_riesgo_cv_framingham_colombia.md` | 38 KB | `minsalud_gpc_dislipidemias_2014_guia27_completa.pdf` | 35, 154-169, 519 | Nota al pie que define la escala de Framingham recalibrada para Colombia como la original multiplicada por 0,75 (p. 35); Seccion 5.5 Evaluacion de riesgo cardiovascular completa (pp. 154-169); consideracion sobre el ajuste por 0,75 (p. 519) |
| `minsalud_gpc_dislipidemias_2014_recomendaciones_y_algoritmos.md` | 25 KB | `minsalud_gpc_dislipidemias_2014_guia27_completa.pdf` | 34-49 | Resumen de recomendaciones incluidas metas de manejo, y algoritmos de tamizacion, evaluacion del riesgo cardiovascular, tratamiento, monitorizacion y seguimiento (pp. 34-49) |
| `minsalud_lineamientos_ecv_2026_hogar_e_intervenciones.md` | 42 KB | `minsalud_lineamientos_ecv_dm_erc_2026.pdf` | 44-62 | Tabla 2 Entorno Hogar; Gestion de las intervenciones individuales incluida deteccion temprana; Tabla 7 factores de riesgo cardiovascular y metabolico en la mujer (pp. 44-62) |
| `rcp_news2_tabla_puntuacion_y_umbrales.md` | 5 KB | `rcp_news2_chart3_observation_chart_2022.pdf`<br>`rcp_news2_chart2_umbrales_disparadores_2017.pdf` | 1-2<br>1-2 | Tabla NEWS2 completa (frecuencia respiratoria, SpO2 escalas 1 y 2, aire/oxigeno, presion sistolica, pulso, consciencia ACVPU, temperatura; puntajes 0-3) y tabla de umbral -> frecuencia de monitoreo -> respuesta clinica |
| `rcp_news2_resumen_ejecutivo_2017.md` | 44 KB | `rcp_news2_executive_summary_2017.pdf` | 1-18 | Documento completo (18 pp.) |
| `rcp_news2_informe_2017_recomendaciones_y_funcionamiento.md` | 46 KB | `rcp_news2_final_report_2017.pdf` | 18-24, 51-60 | Recomendaciones numeradas del grupo de trabajo, incluida la frecuencia minima de monitoreo por puntaje (pp. 18-24); capitulos 6 'How the NEWS works' y 7 'Using the NEWS', con el sistema de puntuacion y la organizacion de la respuesta clinica (pp. 51-60) |
| `mews_tabla_puntuacion_ccby.md` | 27 KB | `mews_nishijima_2016_journal_intensive_care_ccby.pdf` | 1-6 | Articulo completo (pp. 1-6). Table 1 'The modified early warning score (MEWS) system' esta en la p. 2: presion sistolica, frecuencia cardiaca, frecuencia respiratoria, temperatura, nivel de consciencia AVPU y preocupacion sobre el estado del paciente, con puntajes 0-3 |
| `framingham_colombia_munoz_2014.md` | 50 KB | `framingham_procam_colombia_munoz_2014_rcc.pdf` | 1-11 | Articulo completo salvo la ultima pagina de referencias (pp. 1-11): metodos de calibracion, discriminacion y calibracion en la cohorte colombiana |

### Fichas de referencia sin texto completo

Documentos cuya fuente no es de acceso abierto. **No contienen contenido clinico**: son fichas bibliograficas con el estado de acceso.

| Archivo | Fuente | Estado de acceso |
|---|---|---|
| `aha_asa_2021_prevencion_secundaria_acv_ficha.md` | Kleindorfer DO, Towfighi A, Chaturvedi S, et al. 2021 Guideline for the Prevention of Stroke in Patients With Stroke and Transient Ischemic Attack. Stroke. 2021;52(7):e364-e467. DOI 10.1161/STR.0000000000000375. PMID 34024117 | Texto completo RESTRINGIDO: sin PDF abierto, ahajournals responde 403 a clientes automatizados, no depositada en PMC. Las paginas publicas de la AHA declaran 'All rights reserved. Unauthorized use prohibited.' |

---

## PDF originales (`_originales/`)

Tamaños y hashes leídos de `_originales/manifest.tsv`.

| Archivo | Tamaño | SHA256 (12) | URL exacta |
|---|---|---|---|
| `minsalud_gpc_hta_2017_guia18_segunda_edicion.pdf` | 49.6 MB | `c58fdd3af8d5` | https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/DE/CA/gpc-hipertension-arterial-primaria-hta.pdf |
| `minsalud_gpc_hta_2025_guia18_tercera_edicion.pdf` | 6.3 MB | `2a666687fbae` | https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/DE/CA/gpc-actualizacion-parcial-hta-primaria-vc.pdf |
| `minsalud_gpc_hta_2013_pacientes.pdf` | 3.0 MB | `ab29c9b805e1` | https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/DE/CA/gpc-pacientes-hipertension-arterial-hta.pdf |
| `minsalud_gpc_acv_isquemico_2015_guia54_profesionales.pdf` | 4.2 MB | `1321acf7e90e` | https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/DE/CA/gpc-profesionales-ataque-cerebro-vascular-isquemico.pdf |
| `minsalud_gpc_dislipidemias_2014_guia27_completa.pdf` | 7.5 MB | `fbf7daa5cfba` | https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/INEC/IETS/GPC-Dislipidemi-completa.pdf |
| `minsalud_lineamientos_ecv_dm_erc_2026.pdf` | 819 KB | `6d3ef1c5b1d4` | https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/VS/PP/ENT/lineamientos-gestion-enfermedades-cardiovasculares-metabolicas.pdf |
| `rcp_news2_final_report_2017.pdf` | 2.5 MB | `c5dad854ccf0` | https://www.rcp.ac.uk/media/a4ibkkbf/news2-final-report_0_0.pdf |
| `rcp_news2_executive_summary_2017.pdf` | 513 KB | `b4d1a7e02fa6` | https://www.rcp.ac.uk/media/ctulqqbn/news2-executive-summary_0.pdf |
| `rcp_news2_chart2_umbrales_disparadores_2017.pdf` | 98 KB | `069ab296933c` | https://www.rcp.ac.uk/media/2acdezkd/news2-chart-2_news-thresholds-and-triggers_0.pdf |
| `rcp_news2_chart3_observation_chart_2022.pdf` | 616 KB | `cca09814f595` | https://www.rcp.ac.uk/media/eczf5mvm/news2-chart-3_news-observation-chart_2022_0_0.pdf |
| `framingham_procam_colombia_munoz_2014_rcc.pdf` | 600 KB | `6139f7a00513` | https://rccardiologia.com/previos/RCC%202014%20Vol.%2021/RCC_2014_21_4_JUL-AGO/RCC_2014_21_4_202-212.pdf |
| `mews_nishijima_2016_journal_intensive_care_ccby.pdf` | 812 KB | `7f8ae7472b35` | https://link.springer.com/content/pdf/10.1186/s40560-016-0134-7.pdf |

---

## Acceso y licencia por fuente

- **Ministerio de Salud y Proteccion Social de Colombia / IETS. Guia No. 18, tercera edicion, actualizacion parcial 2025**
  - Publico y gratuito (MSPS). Propiedad intelectual segun clausula 12 del contrato interadministrativo 1490 de 2025; sin licencia abierta.
- **Ministerio de Salud y Proteccion Social de Colombia / Colciencias. Guia No. 18, segunda edicion, 2017**
  - Publico y gratuito (MSPS). Derechos patrimoniales Minsalud/Colciencias; sin licencia abierta.
- **Ministerio de Salud y Proteccion Social de Colombia, Guia No. 18, Bogota, abril de 2013**
  - Publico y gratuito (MSPS).
- **Ministerio de Salud y Proteccion Social de Colombia / Colciencias. Guia No. 54, 2015**
  - Publico y gratuito (MSPS). Propiedad intelectual Colciencias/MSPS (convocatoria 613 de 2013); sin licencia Creative Commons.
- **Ministerio de Salud y Proteccion Social de Colombia / Colciencias. Guia No. 54, 2015, anexos clinicos**
  - Publico y gratuito (MSPS). Propiedad intelectual Colciencias/MSPS; sin licencia Creative Commons.
- **Ministerio de Salud y Proteccion Social de Colombia / Colciencias / IETS. Guia No. 27, 2014**
  - Publico y gratuito (MSPS). Derechos patrimoniales Colciencias/MSPS (Ley 23 de 1982); sin licencia abierta.
- **Royal College of Physicians (Reino Unido). NEWS2 observation chart, diciembre de 2022; NEWS2 thresholds and triggers, 2017**
  - Sin restriccion de derechos de autor; el RCP debe ser reconocido en cualquier material reproducido. Graficos marcados (c) Royal College of Physicians.
- **Royal College of Physicians (Reino Unido). NEWS2: Standardising the assessment of acute-illness severity in the NHS**
  - Sin restriccion de derechos de autor; el RCP debe ser reconocido en cualquier material reproducido.
- **Nishijima I, Oyadomari S, et al. Use of a modified early warning score system to reduce the rate of in-hospital cardiac arrest. Journal of Intensive Care 2016. DOI 10.1186/s40560-016-0134-7. PMID 26865981**
  - Acceso abierto, Creative Commons Attribution 4.0 (CC BY 4.0). Redistribuible citando la fuente.
- **Munoz OM, Rodriguez NI, Ruiz A, Rondon M. Revista Colombiana de Cardiologia 2014;21(4):202-212**
  - Descarga publica gratuita desde el sitio de la revista, pero el PDF declara derechos reservados (c) Sociedad Colombiana de Cardiologia y Cirugia Cardiovascular / Elsevier Espana. Indexado en DOAJ. Contradiccion documentada en SOURCES.md.
- **Kleindorfer DO, Towfighi A, Chaturvedi S, et al. 2021 Guideline for the Prevention of Stroke in Patients With Stroke and Transient Ischemic Attack. Stroke. 2021;52(7):e364-e467. DOI 10.1161/STR.0000000000000375. PMID 34024117**
  - Texto completo RESTRINGIDO: sin PDF abierto, ahajournals responde 403 a clientes automatizados, no depositada en PMC. Las paginas publicas de la AHA declaran 'All rights reserved. Unauthorized use prohibited.'

---

## Pendiente

- Nada: todos los extractos del spec están construidos.

- **AHA/ASA:** decidir si se incluye el resumen público de la guía **2021** de prevención secundaria, marcado explícitamente como resumen y no como texto completo.

---

## Correcciones a lo que se había asumido

Cuatro cosas resultaron distintas de lo esperado. Van aquí porque cambian qué se puede
citar y con qué fecha.

### 1. El PDF de "actualización parcial" es la tercera edición de 2025, no la de 2016

La URL `gpc-actualizacion-parcial-hta-primaria-vc.pdf` entrega hoy la **guía completa,
Guía No. 18, tercera edición, actualización parcial 2025** (1.175 páginas, MSPS + IETS,
contrato interadministrativo 1490 de 2025) — no una versión corta de 2016. El archivo se
renombró a `minsalud_gpc_hta_2025_guia18_tercera_edicion.pdf` para que el nombre no
mienta. **Es la guía colombiana de HTA más reciente disponible**, y eso mejora la base.

### 2. El PDF "profesionales" de HTA es la segunda edición de 2017, no la de 2013

Los encabezados internos dicen «Guía No 18 | 2017» y la edición de 2025 se refiere a él
como «la GPC 2017». Renombrado a `minsalud_gpc_hta_2017_guia18_segunda_edicion.pdf`.

**Se conserva a propósito:** la actualización de 2025 dice reemplazar *algunas* de sus
recomendaciones, no todas. Las no priorizadas para actualización siguen vigentes, así que
las dos ediciones conviven en la base. Al citar un umbral hay que mirar cuál de las dos
lo respalda.

### 3. No existe una guía AHA/ASA 2024 de prevención secundaria de ACV

| Lo que se buscaba | Lo que existe |
|---|---|
| «AHA/ASA 2024, prevención secundaria» | **2024 Guideline for the *Primary* Prevention of Stroke**, DOI 10.1161/STR.0000000000000475 |
| — | **2021 Guideline for the Prevention of Stroke in Patients With Stroke and Transient Ischemic Attack** — la de prevención *secundaria* — DOI 10.1161/STR.0000000000000375, *Stroke* 2021;52:e364–e467 |

La relevante para HomecareCCV es la de **2021**: sus pacientes ya tuvieron el evento.

**No se descargó ninguna de las dos.** `ahajournals.org` responde 403 a descarga
automatizada y no ofrece PDF abierto. Páginas públicas utilizables, si se decide incluir
un resumen marcado como tal:

- Hub de la guía 2021: https://professional.heart.org/en/guidelines-statements/2021-guideline-for-the-prevention-of-stroke-in-patients-with-stroke-andstr0000000000000375
- Resumen público 2021: https://professional.heart.org/en/science-news/2021-guideline-for-the-prevention-of-stroke-in-patients-with-stroke-and-transient-ischemic-attack
- Resumen público 2024: https://professional.heart.org/en/science-news/2024-guideline-for-the-primary-prevention-of-stroke
- PubMed 2021: https://pubmed.ncbi.nlm.nih.gov/34024117/

Cualquier archivo derivado de ahí debe llamarse `..._resumen_publico.md` y declarar en el
encabezado que **es resumen ejecutivo, no el texto completo de la guía.**

### 4. El artículo original de MEWS está tras muro de pago

Subbe CP, Kruger M, Rutherford P, Gemmel L. *Validation of a modified Early Warning Score
in medical admissions.* QJM 2001;94(10):521–526 (PMID 11588210). En Oxford Academic solo
el resumen es público.

La tabla MEWS se toma de una fuente **CC BY 4.0** que la reproduce: Nishijima I,
Oyadomari S, et al., *Journal of Intensive Care* 2016, DOI 10.1186/s40560-016-0134-7
(PMID 26865981, PMC4748572). La original se cita como referencia primaria.


---

## Dos decisiones de implementación que conviene revisar

### Los PDF originales quedaron en `_originales/`, no en la raíz de `documents/`

La instrucción era conservar el PDF original junto al extracto. Se cumple —
`_originales/` está dentro de `backend/rag/documents/` — pero **no en la raíz**, y la
razón es concreta: `embeddings.py` y `retriever.py` hacen `documents_dir.glob("*")` e
indexan también los `.pdf`. Poner los PDF arriba haría que **cada guía entre dos veces al
índice**: una por el extracto curado y otra por el PDF completo. Sobre una guía de 1.175
páginas eso no es una redundancia menor, es ahogar el índice.

`glob("*")` no entra en subdirectorios, así que `_originales/` conserva la procedencia sin
contaminar el índice. Si prefieres los PDF en la raíz, hay que filtrarlos primero en el
indexador.

### `SOURCES.md` y `README.md` sí se están indexando

Por la misma razón: son `.md` en la raíz de `documents/`. Este archivo es metadata de
procedencia, no contenido clínico, y ahora mismo entraría al índice como si lo fuera. Un
filtro de una línea en `build_document_chunks` lo resuelve:

```python
EXCLUIDOS = {"README.md", "SOURCES.md"}
for path in sorted(documents_dir.glob("*")):
    if path.name in EXCLUIDOS or path.name.startswith("."):
        continue
```

No se aplicó porque toca código que no se pidió tocar.

