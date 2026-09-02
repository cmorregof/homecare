# Manual de CARMEN · Salud cardiaca
#
#   make          compila manual.pdf (dos pasadas, por el índice)
#   make clean    borra los archivos auxiliares
#   make limpio   borra también el PDF

MAIN = manual

$(MAIN).pdf: $(MAIN).tex $(wildcard figuras/*)
	pdflatex -interaction=nonstopmode $(MAIN).tex
	pdflatex -interaction=nonstopmode $(MAIN).tex

clean:
	rm -f $(MAIN).aux $(MAIN).log $(MAIN).out $(MAIN).toc

limpio: clean
	rm -f $(MAIN).pdf

.PHONY: clean limpio
