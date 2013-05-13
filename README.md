Prototype of Cloud Kepler
=========================
Pipeline for processing Kepler Space Telescope time series and search
for planets.

More on the project on:
http://kepler.nasa.gov/
http://keplergo.arc.nasa.gov/PyKE.shtml

More on Python Map-Reduce on:
http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/


### Set-up and activate Virtualenv with no SUDO use
```
cd ~/temp
curl -L -o virtualenv.py https://raw.github.com/pypa/virtualenv/master/virtualenv.py
python virtualenv.py cloud-kepler --no-site-packages
. cloud-kepler/bin/activate
pip install pyfits numpy simplejson
```

Test that the basic python code is working:
```
cat {DIRECTORY_WITH_CLOUD_KEPLER}/test/test_q1.txt | python {DIRECTORY_WITH_CLOUD_KEPLER}/python/download.py
```

If it starts downloading and spewing base64 encoded numpy arrays, then
you're good. 

### References
* Koch, D.G., Borucki, W.J., Basri, G., et al. 2010, The Astrophysical
  Journal Letters, 713, L79 [10.1088/2041-8205/713/2/L79](http://adsabs.harvard.edu/abs/2010ApJ...713L..79K)
* Kovacs, G., Zucker, S., & Mazeh, T. 2002, Astronomy & Astrophysics,
  391, 369 [10.1051/0004-6361:20020802] (http://adsabs.harvard.edu/abs/2002A%26A...391..369K)
* Still, M., & Barclay, T. 2012, Astrophysics Source Code Library, 8004
