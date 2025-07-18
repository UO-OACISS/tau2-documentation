
USER_GUIDE_SRC      := src/modules/ROOT/pages/usersguide/usersguide.adoc
INSTALL_GUIDE_SRC   := src/modules/ROOT/pages/installguide/installguide.adoc
REFERENCE_GUIDE_SRC := src/modules/ROOT/pages/referenceguide/referenceguide.adoc
BUILD_DIR           := build
HTML_SINGLE_DIR     := $(BUILD_DIR)/html-single
PDF_DIR             := $(BUILD_DIR)/pdf
CHUNKED_DIR         := $(BUILD_DIR)/chunked-html
USER_GUIDE_HTML      := $(HTML_SINGLE_DIR)/user-guide.html
INSTALL_GUIDE_HTML   := $(HTML_SINGLE_DIR)/install-guide.html
REFERENCE_GUIDE_HTML := $(HTML_SINGLE_DIR)/reference-guide.html
USER_GUIDE_PDF      := $(PDF_DIR)/user-guide.pdf
INSTALL_GUIDE_PDF   := $(PDF_DIR)/install-guide.pdf
REFERENCE_GUIDE_PDF := $(PDF_DIR)/reference-guide.pdf
ANTORA_PLAYBOOK := antora-playbook.yml

ASCIIDOCTOR_FLAGS = -a imagesdir=../../assets/images
ASCIIDOCTOR_PDF_FLAGS = $(ASCIIDOCTOR_FLAGS) -a pdf-stylesdir=themes -a pdf-style=tau

.PHONY: all html-single pdf html-chunked clean

all: html-single pdf html-chunked

html-single: $(USER_GUIDE_HTML) $(INSTALL_GUIDE_HTML) $(REFERENCE_GUIDE_HTML)
	@echo "Single-page HTML generation complete."

pdf: $(USER_GUIDE_PDF) $(INSTALL_GUIDE_PDF) $(REFERENCE_GUIDE_PDF)
	@echo "PDF generation complete."

html-chunked:
	@mkdir -p $(CHUNKED_DIR)
	npx antora --stacktrace --to-dir $(CHUNKED_DIR) $(ANTORA_PLAYBOOK)

$(USER_GUIDE_HTML): $(USER_GUIDE_SRC)
	@mkdir -p $(HTML_SINGLE_DIR)
	asciidoctor $(ASCIIDOCTOR_FLAGS) -D $(HTML_SINGLE_DIR) -o $(notdir $@) $<

$(USER_GUIDE_PDF): $(USER_GUIDE_SRC)
	@mkdir -p $(PDF_DIR)
	asciidoctor-pdf $(ASCIIDOCTOR_PDF_FLAGS) -D $(PDF_DIR) -o $(notdir $@) $<

$(INSTALL_GUIDE_HTML): $(INSTALL_GUIDE_SRC)
	@mkdir -p $(HTML_SINGLE_DIR)
	asciidoctor $(ASCIIDOCTOR_FLAGS) -D $(HTML_SINGLE_DIR) -o $(notdir $@) $<

$(INSTALL_GUIDE_PDF): $(INSTALL_GUIDE_SRC)
	@mkdir -p $(PDF_DIR)
	asciidoctor-pdf $(ASCIIDOCTOR_PDF_FLAGS) -D $(PDF_DIR) -o $(notdir $@) $<

$(REFERENCE_GUIDE_HTML): $(REFERENCE_GUIDE_SRC)
	@mkdir -p $(HTML_SINGLE_DIR)
	asciidoctor $(ASCIIDOCTOR_FLAGS) -D $(HTML_SINGLE_DIR) -o $(notdir $@) $<

$(REFERENCE_GUIDE_PDF): $(REFERENCE_GUIDE_SRC)
	@mkdir -p $(PDF_DIR)
	asciidoctor-pdf $(ASCIIDOCTOR_PDF_FLAGS) -D $(PDF_DIR) -o $(notdir $@) $<

clean:
	@rm -rf $(BUILD_DIR) src Makefile antora-playbook.yml
