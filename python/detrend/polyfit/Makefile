.PHONY: default clean

default: polyfit.pyx setup.py
	python setup.py build_ext --inplace
	mv polyfit.so ..

clean:
	rm -rf build polyfit.c

