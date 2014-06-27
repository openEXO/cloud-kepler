.PHONY: clean

default: bls_pulse.pyx bls_pulse_extern.c setup.py
	export CC=gcc
	python setup.py build_ext --inplace

clean:
	rm -rf build bls_pulse.c bls_pulse.so

