#!/bin/bash
#Check that command line args are provided
if ! [ $# -eq 1 ]
  then
    echo "Expected 1 argument: Threshold to report over"
    echo "IE: '$0 90'  -> Will send emails if disks are above 90% full"
    exit 1
fi
#set input as threshold variable
THRESH=$1

#Check input/threshold is a number
re='^[0-9]+$'
if ! [[ $THRESH =~ $re ]]
  then 
    echo "Argument supplied is not a number. Execpts a number between 0 and 100"
    exit 1
fi
#Email addresses to send notifications to
EMAILS='sample_email@server.com'
#Name of the machine that is running the script
HOST=`hostname`
#Header line to print in the email
REPORT="There is a disk on $HOST whose capacity is over $THRESH %\n"

#Get a report of the disk space usage
#Format it to be space delimited
#print out the report line if the disks capacity is detected to be greater than the specified threshold
#Save echo output of the loop to a variable 
OUTPUT=$(df -PBg  | sed 's/ \+/ /g'  | while read fs bl used avail cap mount rest
do
#Extract the total usge of the disk 
REMAIN=`echo $cap | sed 's/%//g'`
#Check its a number
if [[ $REMAIN =~ $re ]] ; then
  #Check if USAGE is greater than the threshold
  if [ $REMAIN -gt $THRESH ]; then
    #Write output to a variable
    echo -e "Disk is $cap% full!\t${used} GB used\t${avail}GB remaining on $fs"
  fi
fi
done)

#Send if we detect the word 'full!' in the output
echo $OUTPUT | grep -q "full!"
SEND=$?
if [ $SEND -eq 0 ]; then
  echo -e "$REPORT\n$OUTPUT "  | mail -s "WARNING: Disk approaching capacity" ${EMAILS}
fi
