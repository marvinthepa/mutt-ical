mutt-ical.py is meant as a simple way to display and reply to ical invitations from mutt.

Warning
-------

This script was written during a few days in 2013 for Python 2. I currently do
not use it myself. There might be still issues with recent versions of Python 3.

If this script does not work for you, please consider fixing it yourself. It
is just a few lines of code after all.

Pull requests are accepted, but please do not expect me to test them, they
will be merged after a quick and shallow review.

You have been warned.

Installing
----------

* Copy it into somewhere in your PATH, (or you can specify the PATH in your .mailcap)
* Edit your mailcap (~/.mailcap or /etc/mailcap) to have the following line:

```
# for replying
text/calendar; <path>mutt-ical.py -i -e "user@domain.tld" %s
application/ics; <path>mutt-ical.py -i -e "user@domain.tld" %s
# for auto-view
text/calendar; <path>mutt-ical.py -D -e "user@domain.tld" %s; copiousoutput
application/ics; <path>mutt-ical.py -D -e "user@domain.tld" %s; copiousoutput
```

* if you want to use auto view in the pager, use something like the following in .muttrc
   (just an example, configure text/plain and text/html at your own discretion)

```
auto_view text/calendar text/plain text/html
alternative_order text/calendar text/plain text/html
```

(Don't forget to add your email address)

OSX Users
---------

* For added fun on OSX, you can extend it to the following, to get iCal to open it nicely too (iCal cares not for mime types it seems):
```
text/calendar; mv %s %s.ics && open %s.ics && <path>mutt-ical.py -i -e "user@domain.tld" %s.ics && rm %s.ics
```
* You can force iCal to stop trying to send mail on your behalf by replacing
the file /Applications/iCal.app/Contents/Resources/Scripts/Mail.scpt with your
own ActionScript. I went with the following: `error number -128`
Which tells it that the user cancelled the action.

    * Open AppleScript Editor, paste the code from above into a new script, then save it.
    * Move the old script /Applications/iCal.app/Contents/Resources/Scripts/Mail.scpt just in case you want to re-enable the functionality.
    * Copy your new script into place.

Usage
-----

If you configure auto_view (see above), the description should be visible in
the pager.

To reply, just open the ical file from mutt:
* View the attachements (usually 'v')
* Select the text/calendar entry
* Invoke the mailcap entry (usually 'm')
* Choose your reply

An old sendmail wrapper is also included, but since mutt's SMTP support has now improved, rather configure your SMTP settings through mutt's config. The wrapper is kept in case someone finds it useful. However, the get_mutt_command function will need the relevant code uncommented to use it.

Requirements
------------

mutt, python, bash, vobject:
http://vobject.skyhouseconsulting.com/ or 'easy_install vobject'

Inspired by:
* http://weirdzone.ru/~veider/accept.py
* http://vpim.rubyforge.org/files/samples/README_mutt.html
