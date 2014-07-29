.PHONY: default clean html-docs latex-docs

default:
	cd bls_pulse_cython; make
	cd detrend; make

html-docs:
	sphinx-build -b html ../docs ../docs/_build

latex-docs:
	sphinx-build -b latex ../docs ../docs/_build

clean:
	cd bls_pulse_cython; make clean
	cd detrend; make clean
	rm -f *.pyc

