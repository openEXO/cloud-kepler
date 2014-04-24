Prototype of Cloud Kepler ![Logo](https://travis-ci.org/openEXO/cloud-kepler.svg?branch=master)
=========================
Pipeline for processing Kepler Space Telescope time series and search
for planets.

More on the Kepler project on:
* http://kepler.nasa.gov/

* http://keplergo.arc.nasa.gov/PyKE.shtml

More on Python Map-Reduce on:
* http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/

More on Amazon Elastic Map-Reduce and Hadoop:
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

Install Oracle VM VirtualBox 4.2.14 from VirtualBox-4.2.14-86644-win from https://www.virtualbox.org/wiki/Downloads

Extract cloudera-quickstart-demo-vm-4.3.0-virtualbox.tar.gz from https://ccp.cloudera.com/display/SUPPORT/Cloudera+QuickStart+VM

Enter the created folder and extract cloudera-quickstart-demo-vm-4.3.0-virtualbox.tar, you should end up with cloudera-quickstart-demo-vm.ovf and cloudera-quickstart-demo-vm.vmdk in whatever folder you extracted to

Open up Oracle VM VirtualBox Manager

Select the New icon, the Create Virtual Machine window boots up.

For operating system, select Linux and Ubuntu

For memory size, select 4096 MB

For Hard Drive, select "Use an existing virtual hard drive" and path to cloudera-quickstart-demo-vm.vmdk

Press Create. Virtual machine now selectable in the main window on virtualbox manager.

Press the Settings button, opens the settings window.

Choose the system tab

Change chipset to ICH9, make sure "Enable IO APIC" is checked.

Select it and pressed Start, boot begins, this part takes a little while.

If it gets stuck on any one step for more than 20 minutes, you can assume something is wrong.

Eventually the boot sequence will end and you will see a desktop in your virtual machine. Success!


WordCount Example:
Note that this readme assumes a cloudera vm distribution of hadoop.

Inside your virtual machine, go to the Cloudera Hadoop Tutorial at http://www.cloudera.com/content/cloudera-content/cloudera-docs/HadoopTutorial/CDH4/Hadoop-Tutorial/ht_topic_5_1.html

Copy the source code for WordCount and past it into the gedit text editor. Save as WordCount.java in the cloudera's home folder.

Per the instructions there, open terminal, cd to the home directory, then run as follows

```
mkdir wordcount_classes
javac -cp /usr/lib/hadoop/*:/usr/lib/hadoop/client-0.20/* -d wordcount_classes WordCount.java
```

Right click on the wordcount_classes folder you made (it will be in the home directory) and select compress. Choose .jar as the file format and wordcount as filename.

```
echo "Hello World Bye World" > file0
echo "Hello Hadoop Goodbye Hadoop" > file1
hadoop fs -mkdir /user/cloudera /user/cloudera/wordcount /user/cloudera/wordcount/input
hadoop fs -put file* /user/cloudera/wordcount/input
hadoop jar wordcount.jar org.myorg.WordCount /user/cloudera/wordcount/input output
```

According to the Cloudera Tutoria, this should be all you need to do, but I got an error message here, so everything is not quite right yet.

When you first log onto the virtual machine, it should begin with a firefox window open to some kind of cloudera page. Go to this and click the Cloudera Manager link.

Enter 'admin' and 'admin' as a username and password to access it.

Now you can see the health of your setup's various components. mapreduce1 will probably be listed as in poor health. click on it

You should see that the jobtracker is the problem. return to terminal.
```
sudo -u hdfs hadoop fs -mkdir /tmp/mapred/system
sudo -u hdfs hadoop fs -chown mapred:hadoop /tmp/mapred/system
```

Then restart jobtracker by clicking instances the instances tab, clicking on jobtracker, clicking to the processes tab, selecting the actions tab in the corner, and selecting restart.

```
hadoop jar wordcount.jar org.myorg.WordCount /user/cloudera/wordcount/input output
```

This time it should work.

```
hadoop fs -cat output/part-00000
```

This will open up the output folder for you from the hadoop run.

It should look like this:
"
Bye 1

Goodbye 1

Hadoop 2

Hello 2

World 2
"
If it looks like that then you are good.

It is worth noting that Hadoop won't work unless the directory you set as your output both does not currently exist and is in your hadoop fs home directory.

## Lein setup
Note that this readme assumes a cloudera vm distribution of hadoop.

You can find Lein at https://github.com/technomancy/leiningen

Download the script from https://raw.github.com/technomancy/leiningen/stable/bin/lein and place it wherever you want

```
export $HOME=/home
cd
cd ..
cd etc/profile.d
sudo vim lein.sh
```

On one line of the file write 'export PATH=$PATH:{wherever your lein file is located}` (in my case /home/cloudera/Desktop)

Save the file and exit.

Exit and reenter terminal to get back to you home directory.

```
chmod 755 {location of lein}
```

Lein should now be functioning, call 'lein' in terminal to test.

## LEMUR set-up 
Note that this readme assumes a cloudera vm distribution of hadoop.

Lemur can be downloaded from  http://download.climate.com/lemur/releases/lemur-1.3.1.tgz. follow that link and the file should appear in your download folder.

Extract it, and then put it wherever you want it to be.

```
export $HOME=/home
cd
cd ..
cd etc/profile.d
sudo vim lemur.sh
```

You are now writing a file which will allow your system to recognize lemur.

on the first line of the file write 'export LEMUR_HOME={wherever you saved your lemur file}' (in my case /home/cloudera/Desktop/lemur).

on the second line of the file write 'export LEMUR_AWS_ACCESS_KEY={your aws access key}'

on the third line of the file write 'export LEMUR_AWS_SECRET_KEY={your aws secret key}'

on the fourth line of the file write 'export PATH=$PATH:$LEMUR_HOME/bin'

save the file and exit.

Lemur should now work, call 'lemur' in terminal to test.

# References
* Koch, D.G., Borucki, W.J., Basri, G., et al. 2010, The Astrophysical
  Journal Letters, 713, L79 [10.1088/2041-8205/713/2/L79](http://adsabs.harvard.edu/abs/2010ApJ...713L..79K)
* Kovacs, G., Zucker, S., & Mazeh, T. 2002, Astronomy & Astrophysics,
  391, 369 [10.1051/0004-6361:20020802] (http://adsabs.harvard.edu/abs/2002A%26A...391..369K)
* Still, M., & Barclay, T. 2012, Astrophysics Source Code Library, 8004
* LEMUR launcher, Limote M. et al. 2012 [The Climate Corporation](https://github.com/TheClimateCorporation/lemur)
