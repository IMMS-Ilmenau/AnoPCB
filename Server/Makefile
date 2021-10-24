clean:
	python setup.py clean

build: clean
	python setup.py bdist_wheel

install: build
	pip install --force-reinstall dist/anopcb_server-2.0-py3-none-any.whl

.PHONY: clean build install all

all: clean build install