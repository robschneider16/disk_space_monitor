# disk_space_monitor
A simple script to monitor disk usage over time as a cronjob 


To run, first edit the script and update the email address you wish to send emails to when disk capacity is almost full.

update the variable
EMAILS='sample_email@server.com'
to 
EMAILS='<Your_email_here>@server.com'

then execute via the command line

$bash disk_space_monitor.bash 90

The argument is the capacity threshold. So in the above example, emails will be sent if the machine sees a disk over 90% full

