USER_GUIDE_SRC      := src/modules/ROOT/pages/usersguide/usersguide.adoc
INSTALL_GUIDE_SRC   := src/modules/ROOT/pages/installguide/installguide.adoc
REFERENCE_GUIDE_SRC := src/modules/ROOT/pages/referenceguide/referenceguide.adoc
BUILD_DIR           := build
HTML_SINGLE_DIR     := $(BUILD_DIR)/html-single
PDF_DIR             := $(BUILD_DIR)/pdf
CHUNKED_DIR         := $(BUILD_DIR)/html-docs
USER_GUIDE_HTML      := $(HTML_SINGLE_DIR)/tau-usersguide.html
INSTALL_GUIDE_HTML   := $(HTML_SINGLE_DIR)/tau-installguide.html
REFERENCE_GUIDE_HTML := $(HTML_SINGLE_DIR)/tau-referenceguide.html
USER_GUIDE_PDF      := $(PDF_DIR)/tau-usersguide.pdf
INSTALL_GUIDE_PDF   := $(PDF_DIR)/tau-installguide.pdf
REFERENCE_GUIDE_PDF := $(PDF_DIR)/tau-referenceguide.pdf
ANTORA_PLAYBOOK := antora-playbook.yml

# Common flags for all Asciidoctor commands
ASCIIDOCTOR_FLAGS = -a imagesdir=../../assets/images

# Correct PDF flags that enable the title page, toc, and custom theme
ASCIIDOCTOR_PDF_FLAGS = $(ASCIIDOCTOR_FLAGS) \
                        -a pdf-theme=./pdf-theme.yml \
                        -a title-page \
                        -a toc \
			-a toclevels=3 \
			 -a list-of-figures=true -a list-of-tables=true
#			-a title-logo-image=$(CURDIR)/src/modules/ROOT/assets/images/NewTauLogo.png

.PHONY: all pdf html-chunked clean

NAV_ADOC = src/modules/ROOT/nav.adoc

all: pdf html-chunked

html-single: $(USER_GUIDE_HTML) $(INSTALL_GUIDE_HTML) $(REFERENCE_GUIDE_HTML)
	@echo "Single-page HTML generation complete."

pdf: $(USER_GUIDE_PDF) $(INSTALL_GUIDE_PDF) $(REFERENCE_GUIDE_PDF)
	@echo "PDF generation complete."

html-chunked: $(NAV_ADOC)
	@mkdir -p $(CHUNKED_DIR)
	npx antora --stacktrace --to-dir $(CHUNKED_DIR) $(ANTORA_PLAYBOOK)

$(NAV_ADOC): $(USER_GUIDE_SRC) $(INSTALL_GUIDE_SRC) $(REFERENCE_GUIDE_SRC) generate_nav.py
	@echo "--- Regenerating navigation file from AsciiDoc sources ---"
	@python3 generate_nav.py

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
	@rm -rf $(BUILD_DIR) $(NAV_ADOC)
