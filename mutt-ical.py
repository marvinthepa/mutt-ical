#!/usr/bin/env python
# -*- coding: utf8 -*-

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
from subprocess import Popen, PIPE
from getopt import gnu_getopt as getopt

usage="""
usage:
%s [OPTIONS] -e your@email.address filename.ics
OPTIONS:
    -i interactive
    -a accept
    -d decline
    -t tentatively accept
    (accept is default, last one wins)
""" % sys.argv[0]

def del_if_present(dic, key):
    if dic.has_key(key):
        del dic[key]

def set_accept_state(attendees, state):
    for attendee in attendees:
        attendee.params['PARTSTAT'][0] = state
        for i in ["RSVP","ROLE","X-NUM-GUESTS","CUTYPE"]:
            del_if_present(attendee.params,i)
    return attendees

def get_accept_decline():
    while True:
        sys.stdout.write("Accept Invitation? [Y/n/t]")
        ans = sys.stdin.readline()
        if ans.lower() == 'y\n' or ans == '\n':
            return 'ACCEPTED'
        elif ans.lower() == 'n\n':
            return 'DECLINED'
        elif ans.lower() =='t\n':
            return 'TENTATIVE'

def get_answer(invitation):
    # create
    ans = vobject.newFromBehavior('vcalendar')
    ans.add('method')
    ans.method.value = "REPLY"
    ans.add('vevent')

    # just copy from invitation
    for i in ["uid", "summary", "dtstart", "dtend", "organizer"]:
        if invitation.vevent.contents.has_key(i):
            ans.vevent.add( invitation.vevent.contents[i][0] )

    # new timestamp
    ans.vevent.add('dtstamp')
    ans.vevent.dtstamp.value = datetime.utcnow().replace(
            tzinfo = invitation.vevent.dtstamp.value.tzinfo)
    return ans

def write_to_tempfile(ical):
    tempdir = tempfile.mkdtemp()
    icsfile = tempdir+"/event-reply.ics"
    with open(icsfile,"w") as f:
        f.write(ical.serialize())
    return icsfile, tempdir

def get_mutt_command(ical, email_address, accept_decline, icsfile):
    accept_decline = accept_decline.capitalize()
    sender = ical.vevent.contents['organizer'][0].value.split(':')[1].encode()
    summary = ical.vevent.contents['summary'][0].value.encode()
    command = ["mutt", "-a", icsfile,
            "-e", 'set sendmail=\'ical_reply_sendmail_wrapper.sh\'',
            "-s", "'%s: %s'" % (accept_decline, summary), "--", sender]
    return command

def execute(command, mailtext):
    process = Popen(command, stdin=PIPE)
    process.stdin.write(mailtext)
    process.stdin.close()

    result = None
    while result is None:
        result = process.poll()
        time.sleep(.1)
    if result != 0:
        print "unable to send reply, subprocess exited with\
                exit code %d\nPress return to continue" % result
        sys.stdin.readline()

if __name__=="__main__":
    email_address = None
    accept_decline = 'ACCEPTED'
    opts, args=getopt(sys.argv[1:],"e:aidt")
    for opt,arg in opts:
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

    if len(args) < 1 or not email_address:
        sys.stderr.write(usage)
        sys.exit(1)

    invitation_file = args[0]
    with open(invitation_file) as f:
        with warnings.catch_warnings(): #vobject uses deprecated Exception stuff
            warnings.simplefilter("ignore")
            invitation = vobject.readOne(f, ignoreUnreadable=True)

    ans = get_answer(invitation)

    attendees = invitation.vevent.contents['attendee']
    set_accept_state(attendees,accept_decline)
    ans.vevent.contents['attendee'] = [i for i in attendees if i.value.endswith(email_address)]
    if len(ans.vevent.contents) < 1:
        sys.stderr.write("Seems like you have not been invited to this event!\n")
        sys.exit(1)

    icsfile, tempdir = write_to_tempfile(ans)

    mutt_command = get_mutt_command(ans, email_address, accept_decline, icsfile)
    mailtext = "'%s has %s'" % (email_address, accept_decline.lower())
    execute(mutt_command, mailtext)

    os.remove(icsfile)
    os.rmdir(tempdir)
