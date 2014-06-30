.PHONY: clean

default: bls_pulse/bls_pulse.pyx bls_pulse/bls_pulse_extern.c bls_pulse/setup.py
	export CC=gcc; cd bls_pulse; python setup.py build_ext --inplace; cp bls_pulse.so ..; cd ..

clean:
	cd bls_pulse; rm -rf build bls_pulse.c bls_pulse.so *.pyc; cd ..
	rm bls_pulse.so

