.PHONY: default, dev-install, upload

default: setup

setup:
	virtualenv -p python venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt -r requirements-dev.txt

dev-install:
	venv/bin/python setup.py develop

clean:
	rm -rf dist
	rm -rf build
	rm -rf encarne.egg-info

dist:
	python setup.py sdist --formats=gztar,zip

upload: clean dist
	twine upload dist/*
