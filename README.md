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
1.install Oracle VM VirtualBox 4.2.14 from VirtualBox-4.2.14-86644-win from https://www.virtualbox.org/wiki/Downloads

1.a. at each point where it asked to install specific hardware. I allow it to install.

2. extract cloudera-quickstart-demo-vm-4.3.0-virtualbox.tar.gz using 7zip. https://ccp.cloudera.com/display/SUPPORT/Cloudera+QuickStart+VM

3. then enter the created folder and extract cloudera-quickstart-demo-vm-4.3.0-virtualbox.tar using 7zip

3.a. end up with cloudera-quickstart-demo-vm.ovf and cloudera-quickstart-demo-vm.vmdk in whatever folder you extracted to

4. open up Oracle VM VirtualBox Manager

5. select the New icon, Create Virtual Machine window boots up.

6. Press Hide Description to get all options at once.

7. For operating system, select Linux and Ubuntu

8. For memory size, select 4096 MB

9. For Hard Drive, select "Use an existing virtual hard drive and pathed to cloudera-quickstart-demo-vm.vmdk

10. Press Create. Virtual machine now selectable in the main window on virtualbox manager.

11. Press the Settings button, opens the settings window.

12. Choose the system tab

13. Change chipset to ICH9, make sure "Enable IO APIC" is checked.

14. Select it and pressed Start, boot begins.

14.a. this part takes a little while.

14.b. However, if it gets stuck on any one step for more than 15 or 20 minutes, you can assume something is wrong.

15. Eventually the boot sequence will end and you will see a desktop in your virtual machine. Success!


WordCount Example:

1. Inside your virtual machine, go to the Cloudera Hadoop Tutorial at http://www.cloudera.com/content/cloudera-content/cloudera-docs/HadoopTutorial/CDH4/Hadoop-Tutorial/ht_topic_5_1.html

2. Copy the source code for WordCount and past it into the gedit text editor. Save as WordCount.java (caps matter) in the cloudera's home folder.

3. Per the instructions there, open terminal, cd to the home directory, then run "mkdir wordcount_classes".

4. Then run "javac -cp /usr/lib/hadoop/*:/usr/lib/hadoop/client-0.20/* -d wordcount_classes WordCount.java

5. right click on the wordcount_classes folder and select compress. Choose .jar as the file format

6. rename your new .jar file wordcount.jar

7. echo "Hello World Bye World" > file0

8. echo "Hello Hadoop Goodbye Hadoop" > file1

9. hadoop fs -mkdir /user/cloudera /user/cloudera/wordcount /user/cloudera/wordcount/input

10. hadoop fs -put file* /user/cloudera/wordcount/input

11. hadoop jar wordcount.jar org.myorg.WordCount /user/cloudera/wordcount/input /user/cloudera/wordcount/output

12. Encounter an error connecting to localhost when hadoop attempts to run.

the guide here looks like it may be of some use

http://www.michael-noll.com/tutorials/running-hadoop-on-ubuntu-linux-single-node-cluster/

however, I am encountering problems setting up a passwordless ssh key per its instructions.

key generation occurs without error, but an attempt to ssh into localhost requests a password, which it should not do.

resolution of this might lead to a smoothly running wordcount.

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
