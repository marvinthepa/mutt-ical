#!/usr/bin/env python3

"""
This script is meant as a simple way to reply to ical invitations from mutt.
See README for instructions and LICENSE for licensing information.
"""

__author__="Martin Sander"
__license__="MIT"

import vobject
import tempfile, time
import os, sys
import warnings
from datetime import datetime
import subprocess
from getopt import gnu_getopt as getopt

from email.message import EmailMessage

usage="""
usage:
%s [OPTIONS] -e your@email.address filename.ics
OPTIONS:
    -i interactive
    -a accept
    -d decline
    -t tentatively accept
    (accept is default, last one wins)
    -D display only
""" % sys.argv[0]

def del_if_present(dic, key):
    if key in dic:
        del dic[key]

def set_accept_state(attendees, state):
    for attendee in attendees:
        attendee.params['PARTSTAT'] = [state]
        for i in ["RSVP","ROLE","X-NUM-GUESTS","CUTYPE"]:
            del_if_present(attendee.params,i)
    return attendees

def get_accept_decline():
    while True:
        sys.stdout.write("\nAccept Invitation? [Y]es/[n]o/[t]entative/[c]ancel\n")
        ans = sys.stdin.readline()
        if ans.lower() == 'y\n' or ans == '\n':
            return 'ACCEPTED'
        elif ans.lower() == 'n\n':
            return 'DECLINED'
        elif ans.lower() =='t\n':
            return 'TENTATIVE'
        elif ans.lower() =='c\n':
            print("aborted")
            sys.exit(1)

def get_answer(invitation):
    # create
    ans = vobject.newFromBehavior('vcalendar')
    ans.add('method')
    ans.method.value = "REPLY"
    ans.add('vevent')

    # just copy from invitation
    for i in ["uid", "summary", "dtstart", "dtend", "organizer"]:
        if i in invitation.vevent.contents:
            ans.vevent.add(invitation.vevent.contents[i][0])

    ans.vtimezone = invitation.vtimezone

    # new timestamp
    ans.vevent.add('dtstamp')
    ans.vevent.dtstamp.value = datetime.utcnow().replace(
            tzinfo = invitation.vevent.dtstamp.value.tzinfo)
    return ans

def execute(command, mailtext):
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    process.stdin.write(mailtext)
    process.stdin.close()

    result = None
    while result is None:
        result = process.poll()
        time.sleep(.1)
    if result != 0:
        print("unable to send reply, subprocess exited with\
                exit code %d\nPress return to continue" % result)
        sys.stdin.readline()

def openics(invitation_file):
    with open(invitation_file) as f:
        invitation = vobject.readOne(f, ignoreUnreadable=True)
    return invitation

def display(ical):
    summary = ical.vevent.contents['summary'][0].value
    if 'organizer' in ical.vevent.contents:
        if hasattr(ical.vevent.organizer,'EMAIL_param'):
            sender = ical.vevent.organizer.EMAIL_param
        else:
            sender = ical.vevent.organizer.value.split(':')[1] #workaround for MS
    else:
        sender = "NO SENDER"
    if 'description' in ical.vevent.contents:
        description = ical.vevent.contents['description'][0].value
    else:
        description = "NO DESCRIPTION"
    if 'attendee' in ical.vevent.contents:
        attendees = ical.vevent.contents['attendee']
    else:
        attendees = ""
    sys.stdout.write("From:\t" + sender + "\n")
    sys.stdout.write("Title:\t" + summary + "\n")
    sys.stdout.write("To:\t")
    for attendee in attendees:
        if hasattr(attendee,'EMAIL_param') and hasattr(attendee,'CN_param'):
            sys.stdout.write(attendee.CN_param + " <" + attendee.EMAIL_param + ">, ")
        else:
            try:
                sys.stdout.write(attendee.CN_param + " <" + attendee.value.split(':')[1] + ">, ") #workaround for MS
            except:
                sys.stdout.write(attendee.value.split(':')[1] + " <" + attendee.value.split(':')[1] + ">, ") #workaround for 'mailto:' in email
    sys.stdout.write("\n")
    if hasattr(ical.vevent, 'dtstart'):
        print("Start:\t%s" % (ical.vevent.dtstart.value.astimezone(tz=None).strftime("%Y-%m-%d %H:%M %z"),))
    if hasattr(ical.vevent, 'dtend'):
        print("End:\t%s" % (ical.vevent.dtend.value.astimezone(tz=None).strftime("%Y-%m-%d %H:%M %z"),))
    sys.stdout.write("\n")
    sys.stdout.write(description + "\n")

def sendmail():
    mutt_setting = subprocess.check_output(["mutt", "-Q", "sendmail"])
    return mutt_setting.strip().decode().split("=")[1].replace('"', '').split()

def organizer(ical):
    if 'organizer' in ical.vevent.contents:
        if hasattr(ical.vevent.organizer,'EMAIL_param'):
            return ical.vevent.organizer.EMAIL_param
        else:
            return ical.vevent.organizer.value.split(':')[1] #workaround for MS
    else:
        raise("no organizer in event")

if __name__=="__main__":
    email_address = None
    accept_decline = 'ACCEPTED'
    opts, args=getopt(sys.argv[1:],"e:aidtD")

    if len(args) < 1:
        sys.stderr.write(usage)
        sys.exit(1)

    invitation = openics(args[0])
    display(invitation)

    for opt,arg in opts:
        if opt == '-D':
            sys.exit(0)
        if opt == '-e':
            email_address = arg
        if opt == '-i':
            accept_decline = get_accept_decline()
        if opt == '-a':
            accept_decline = 'ACCEPTED'
        if opt == '-d':
            accept_decline = 'DECLINED'
        if opt == '-t':
            accept_decline = 'TENTATIVE'

    ans = get_answer(invitation)

    if 'attendee' in invitation.vevent.contents:
        attendees = invitation.vevent.contents['attendee']
    else:
        attendees = ""
    set_accept_state(attendees,accept_decline)
    ans.vevent.add('attendee')
    ans.vevent.attendee_list.pop()
    flag = 1
    for attendee in attendees:
        if hasattr(attendee,'EMAIL_param'):
            if attendee.EMAIL_param == email_address:
                ans.vevent.attendee_list.append(attendee)
                flag = 0
        else:
            if attendee.value.split(':')[1] == email_address:
                ans.vevent.attendee_list.append(attendee)
                flag = 0
    if flag:
        sys.stderr.write("Seems like you have not been invited to this event!\n")
        sys.exit(1)

    summary = ans.vevent.contents['summary'][0].value
    accept_decline = accept_decline.capitalize()
    subject = "'%s: %s'" % (accept_decline, summary)
    to = organizer(ans)

    message = EmailMessage()
    message['From'] = email_address
    message['To'] = to
    message['Subject'] = subject
    mailtext = "'%s has %s'" % (email_address, accept_decline.lower())
    message.add_alternative(mailtext, subtype='plain')
    message.add_alternative(ans.serialize(),
            subtype='calendar',
            params={ 'method': 'REPLY' })

    execute(sendmail() + ['--', to], message.as_bytes())
