Prototype of Cloud Kepler
=========================
Pipeline for processing Kepler Space Telescope time series and search
for planets.

More on the Kepler project on:
* http://kepler.nasa.gov/

* http://keplergo.arc.nasa.gov/PyKE.shtml

More on Python Map-Reduce on:
* http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/

More on Amazon Elasctic Map-Reduce and Hadoop:
* http://aws.amazon.com/elasticmapreduce/

* http://hadoop.apache.org/



# Set-up
## Python and Virtualenv setup
```
cd ~/temp
curl -L -o virtualenv.py https://raw.github.com/pypa/virtualenv/master/virtualenv.py
python virtualenv.py cloud-kepler --no-site-packages
. cloud-kepler/bin/activate
pip install numpy
pip install simplejson
pip install pyfits
```

Test that the basic python code is working:
```
cat {DIRECTORY_WITH_CLOUD_KEPLER}/test/test_q1.txt | python {DIRECTORY_WITH_CLOUD_KEPLER}/python/download.py
```

If it starts downloading and spewing base64 encoded numpy arrays, then
you're good. 

## Hadoop set- up
1.installed Oracle VM VirtualBox 4.2.14 from VirtualBox-4.2.14-86644-win from https://www.virtualbox.org/wiki/Downloads
1.a. at each point where it asked to install specific hardware. I allowed it to install.
2. extracted cloudera-quickstart-demo-vm-4.3.0-virtualbox.tar.gz using 7zip
3. then entered the created folder and extracted cloudera-quickstart-demo-vm-4.3.0-virtualbox.tar using 7zip
3. a. ended up with a series of folders containing cloudera-quickstart-demo-vm.vmdk and cloudera-quickstart-demo-vm.ovf
4. opened up Oracle VM VirtualBox Manager
5. selected the New icon, Create Virtual Machine window booted up.
6. Pressed Hide Description to get all options at once.
7. For operating system, selected Linux and Ubuntu
8. For memory size, selected 4001 MB
9. For Hard Drive, selected "Use an existing virtual hard drive and pathed to cloudera-quickstart-demo-vm.vmdk
10. Pressed Create. Virtual machine now selectable in the main window on virtualbox manager.
11. Selected it and pressed Start, boot begins.
12. Kernel panic - not syncing: Fatal exception
13. Select Power Off
14. Start again
15. Kernel panic - not syncing: Fatal exception
16. Select Power Off
17. Select Remove on machine and Delete All Files
18. Delete the folder housing my .ovf and .vmdk files
19. repeat step 3.
20. Repeat steps 5 to 11 except selecting windows 7 64-bit instead of ubuntu
21. Fold my hands in prayer
22. Repeate steps 12 to 16
23. Contemplate the fact that I got further than this on both monday and tuesday
using the exact same process.
24. Yesterday the exact same process got me to the step "Initializing HDFS" before crashing
25. On monday it booted successfully.
26. trying to unpack rootfs image as initramfs... is the last step seen before things go haywire.
27. Initialize a few more machines with different memory sizes and OS's. Same Result.
28. Give up and post where I am so far, contemplate attempting this on a different machine.

## Lein setup
TODO

## LEMUR set-up 

# References
* Koch, D.G., Borucki, W.J., Basri, G., et al. 2010, The Astrophysical
  Journal Letters, 713, L79 [10.1088/2041-8205/713/2/L79](http://adsabs.harvard.edu/abs/2010ApJ...713L..79K)
* Kovacs, G., Zucker, S., & Mazeh, T. 2002, Astronomy & Astrophysics,
  391, 369 [10.1051/0004-6361:20020802] (http://adsabs.harvard.edu/abs/2002A%26A...391..369K)
* Still, M., & Barclay, T. 2012, Astrophysics Source Code Library, 8004
* LEMUR launcher, Limote M. et al. 2012 [The Climate Corporation](https://github.com/TheClimateCorporation/lemur)
