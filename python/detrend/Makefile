.PHONY: default clean

default: detrend.pyx setup.py
	python setup.py build_ext --inplace
	mv detrend.so ..

clean:
	rm -rf build detrend.c ../detrend.so

