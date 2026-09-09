LATEXMK ?= latexmk
MAIN := main.tex

.PHONY: all clean check check-final
all:
	$(LATEXMK) -lualatex -interaction=nonstopmode -halt-on-error $(MAIN)

check:
	$(LATEXMK) -lualatex -interaction=nonstopmode -halt-on-error $(MAIN)

check-final:
	@perl -ne 'if (/\\(?:placeholder|field|instruction)|TODO|\?\?\?/) { print "$$ARGV:$$.:$$_"; $$bad=1 } END { exit $$bad }' texto/*.tex

clean:
	$(LATEXMK) -C $(MAIN)
