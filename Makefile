RUNTIME_FILES = main.py microdot.py font.py screen.py index.html

.PHONY: setup deploy repl

setup:
	uv pip install --target typings micropython-rp2-pico_w-stubs
	command -v mpremote >/dev/null || uv tool install mpremote

deploy:
	mpremote $(foreach f,$(RUNTIME_FILES),cp $(f) :$(f) +) reset
	@echo "Deployed and reset."

repl:
	mpremote connect auto repl
