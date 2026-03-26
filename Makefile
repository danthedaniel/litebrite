RUNTIME_FILES = main.py microdot.py font.py screen.py index.html

.PHONY: setup deploy

setup:
	uv pip install --target typings -r requirements-dev.txt
	uv tool install mpremote

deploy:
	mpremote $(foreach f,$(RUNTIME_FILES),cp $(f) :$(f) +) reset
	@echo "Deployed and reset."

repl:
	mpremote connect auto repl
