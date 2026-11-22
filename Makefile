PYTHON ?= python3

.PHONY: setup doctor test macos-setup
setup:
	$(PYTHON) -m pip install -r requirements.txt
doctor:
	$(PYTHON) -m android_mtk doctor
test:
	$(PYTHON) -m unittest discover -s tests -p test_android_mtk.py -v
macos-setup:
	bash scripts/setup_macos.sh
