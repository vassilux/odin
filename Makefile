# 'Makefile'
#HTML := $(patsubst %.md,%.html,$(wildcard *.md))
PDF := $(patsubst %.md,%.pdf,$(wildcard *.md))
HTML := $(patsubst %.md,%.html,$(wildcard *.md))

all: $(HTML) $(PDF) package

doc-html: $(HTML)

package: $(HTML) $(PDF)
	./prepare_deploy.sh

doc-pdf: $(PDF)
#
%.html: %.md
	pandoc $< -o $@

%.pdf: %.md
	pandoc $< -o $@

clean:
	rm -f $(PDF)
	rm -f $(HTML)
	rm -f *.bak *~

rebuild: clean all


