tox: clean test
install:
	pip install -r requirements-dev.txt
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -r -f *.egg-info
	rm -r -f .cache
	rm -r -f .eggs
	rm -r -f .tox
	rm -r -f build
	rm -r -f dist
sdist: clean
	python setup.py sdist
test:
	rm -f .python-version
	tox
	pyenv local aiolibs
doc:
	cd docs && make html
testpypi: clean
	pip install wheel
	python setup.py sdist bdist_wheel upload -r testpypi
pypi: clean
	pip install wheel
	python setup.py sdist bdist_wheel upload
