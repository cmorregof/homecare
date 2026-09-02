# Manual de CARMEN · Salud cardiaca

Manual de uso y estado del sistema: qué es, cómo se pone en marcha, qué rutas
tiene, cómo entra una medición, cómo funciona el sistema visual y qué
decisiones quedan abiertas.

- **`manual.tex`** — fuente
- **`manual.pdf`** — compilado (14 páginas)
- **`figuras/`** — capturas de la aplicación en ejecución

## Compilar

```
make
```

o a mano:

```
pdflatex manual.tex
pdflatex manual.tex   # la segunda pasada resuelve el índice
```

## Requisitos

Instalación estándar de TeX Live. En Debian o Ubuntu:

```
sudo apt-get install texlive-latex-base texlive-latex-recommended \
                     texlive-fonts-recommended texlive-lang-spanish lmodern
```

El documento usa solo `graphicx`, `xcolor`, `geometry`, `hyperref`,
`booktabs`, `fancyhdr`, `listings`, `babel` y `lmodern`, todos incluidos en
esos paquetes. No requiere `titlesec`, `tcolorbox` ni `enumitem`.
