.PHONY: default clean

default:
	cd bls_pulse_cython; make
	cd detrend/polyfit; make

clean:
	cd bls_pulse_cython; make clean
	cd detrend/polyfit; make clean
	rm -f *.so *.pyc

