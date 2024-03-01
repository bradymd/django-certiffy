## WHAT IS django-certiffy?
It's a django implementation of a certificate monitoring/management system.

## WHO IS IT FOR?
Well sysadmin's in the public sector who want have 30-1000's of certificates that they have to manage/monitor.

## WHAT DOES IT REALLY DO?
It is designed to email contacts as the certificate approach expirey. There is a template for the mailing, and a schedule. 

It will nudge once a day until it expires.

It can generate Certificate Signing Requests and Keys if that is helpful for you.

It can keep track of notes for each certificate - who they are for, notes on how they cert is deployed.

It can grade the certifcate using Qualys ssllabs API. Helpful for keeping track of the qualify of your estate.

If you have hundreds like I do, it can you guage workload, see the waves of certificates that approach.

## WHAT ISN'T IT?
It's not involved with ACME so no auto renewals going on here. But can still keep track of your these certs - I guess they should never expire cos the ACME scheme is working.

## WHY DJANGO and PYTHON and SQLLITE?
Well I have tried a python flask version and this is just another iteration. It's a fairly small implementation - worth looking at perhaps if you are starting out with django. It was really about developing my python skills. 

## HOW ELSE CAN I MANAGE CERTIFICATES?
You will have something from your certificate issuer.

You can use nagios (open source monitoring).

## IS IT SECURE?
Well I have put in a USER/ADMIN user system with passwords but I wouldn't put this internet facing really as I'm not experienced enough. It's for your intranet.

## CAN I CONTRIBUTE?
Please do. Should it be in made into a docker container?


