#!/bin/bash

# get $sendmail from mutt
SENDMAIL=`mutt -D|awk -F= '/^sendmail=/{print $2}' | sed -s 's/"//g'`

# fix header for ical reply and pipe to sendmail
sed '/^Content-Type: text\/calendar;/s/$/; METHOD="REPLY"/' | $SENDMAIL "$@"
