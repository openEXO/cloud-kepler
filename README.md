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

4. Then run "javac -cp /usr/lib/hadoop/*:/usr/lib/hadoop/client-0.20/* -d wordcount_classes WordCount.java" to set up an executable map reduce from that java file.

5. right click on the wordcount_classes folder you made (it will be in the home directory) and select compress. Choose .jar as the file format and wordcount as filename.

6. echo "Hello World Bye World" > file0

7. echo "Hello Hadoop Goodbye Hadoop" > file1, these commands generate your input files.

8. run 'hadoop fs -mkdir /user/cloudera /user/cloudera/wordcount /user/cloudera/wordcount/input'

9. then 'hadoop fs -put file* /user/cloudera/wordcount/input' this sets up your input directory

10. 'hadoop jar wordcount.jar org.myorg.WordCount /user/cloudera/wordcount/input output' to run hadoop

11. According to the Cloudera Tutoria, this should be all you need to do, but I got an error message here, so everything is not quite right yet.

12. When you first log onto the virtual machine, it should begin with a firefox window open to some kind of cloudera page. Click the Cloudera Manager link.

13. Enter 'admin' and 'admin' as a username and password to access it.

14. Now you can see the health of your setup's various components. mapreduce1 will probably be listed as in poor health. click on it

15. You should see that the jobtracker is the problem. return to terminal and type 'sudo -u hdfs hadoop fs -mkdir /tmp/mapred/system'

16. then 'sudo -u hdfs hadoop fs -chown mapred:hadoop /tmp/mapred/system'

17. then restart jobtracker by clicking instances the instances tab, clicking on jobtracker, clicking to the processes tab, selecting the actions tab in the corner, and selecting restart.

18. after it restarts, repeat step 10 to run hadoop again.

19. call 'hadoop fs -ls', an output folder should have appeared in the hadoop fs home directory.

20. call 'hadoop fs -cat output/part-00000', this will print the output of your wordcount.

It should look like this:

Bye 1

Goodbye 1

Hadoop 2

Hello 2

World 2

ps: future calls to hadoop will fail unless you delete the 'output' directory, or set hadoop to create a differently named output folder.

## Lein setup
TODO

## LEMUR set-up 

hop on your cloudera vm (or whatever machine you have hadoop up and running on) and go to https://github.com/TheClimateCorporation/lemur

lemur can be downloaded from  http://download.climate.com/lemur/releases/lemur-1.3.1.tgz. follow that link and the file should appear in your download folder.

extract it, and then put it wherever you want it to be, doesn't even matter

the weird permissions and filesystem of the cloudera vm make this next part sort of annoying. anyway, open up terminal and follow along.

'echo $HOME' this should print /home/cloudera. We can't access what we need to access from this directory so we need to go a little higher.

'export $HOME=/home' and then 'cd' to get yourself into the higher directory.

then 'ls -a' to see all folders in home. 'cd ..' takes you where you need to go.

'cd etc'

'cd profile.d' this is the folder where we need to set up our new environment variable.

'sudo vim lemur.sh' initializes the file.

on the first line of the file write 'export LEMUR_HOME={wherever you saved your lemur file}' (in my case /home/cloudera/Desktop/lemur).

on the second line of the file write 'export LEMUR_AWS_ACCESS_KEY={your aws access key}'

on the third line of the file write 'export LEMUR_AWS_SECRET_KEY={your aws secret key}'

on the fourth line of the file write 'export PATH=$PATH:$LEMUR_HOME/bin'

save the file and exit.

if you re-enter terminal, you will now be able to call lemur from it. I think that means it works.

# References
* Koch, D.G., Borucki, W.J., Basri, G., et al. 2010, The Astrophysical
  Journal Letters, 713, L79 [10.1088/2041-8205/713/2/L79](http://adsabs.harvard.edu/abs/2010ApJ...713L..79K)
* Kovacs, G., Zucker, S., & Mazeh, T. 2002, Astronomy & Astrophysics,
  391, 369 [10.1051/0004-6361:20020802] (http://adsabs.harvard.edu/abs/2002A%26A...391..369K)
* Still, M., & Barclay, T. 2012, Astrophysics Source Code Library, 8004
* LEMUR launcher, Limote M. et al. 2012 [The Climate Corporation](https://github.com/TheClimateCorporation/lemur)
