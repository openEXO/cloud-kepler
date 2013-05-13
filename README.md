Prototype of Cloud Kepler
=========================
Pipeline for processing Kepler Space Telescope time series and search
for planets.

More on the project on:
http://kepler.nasa.gov/
http://keplergo.arc.nasa.gov/PyKE.shtml

More on Python Map-Reduce on:
http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/



*** Dependecies setup
**Set-up and activate Virtualenv with no SUDO use
cd ~/temp
curl -L -o virtualenv.py https://raw.github.com/pypa/virtualenv/master/virtualenv.py
python virtualenv.py cloud-kepler --no-site-packages
. cloud-kepler/bin/activate

**Set-up python code dependencies
pip install pyfits numpy simplejson

**Test that the basic python code is working
cat {DIRECTORY_WITH_CLOUD_KEPLER}/test/test_q1.txt | python {DIRECTORY_WITH_CLOUD_KEPLER}/python/download.py
If it starts downloading and spewing base64 encoded numpy arrays, then
you're good. 
