.PHONY: default clean

default: bls_pulse_cython.pyx bls_pulse_extern.c setup.py
	python setup.py build_ext --inplace
	mv bls_pulse_cython.so ..

clean:
	rm -rf build bls_pulse_cython.c

