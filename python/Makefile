.PHONY: clean

default: bls_pulse_cython/bls_pulse_cython.pyx bls_pulse_cython/bls_pulse_extern.c bls_pulse_cython/setup.py
	cd bls_pulse_cython; python setup.py build_ext --inplace; mv bls_pulse_cython.so ..; cd ..

clean:
	cd bls_pulse_cython; rm -rf build bls_pulse_cython.c bls_pulse_cython.so *.pyc; cd ..
	rm bls_pulse_cython.so

