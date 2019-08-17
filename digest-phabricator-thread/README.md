Take a thread of messages from phabricator in mutt and display them all at
once in vim, filtering out unimportant stuff.

* it's a horrible hack and often breaks
* it's python2. I gave up rewrite to 3 after many bytes() vs str() typecasts.
* it runs vim directly from python
* rather than using `requirements.txt` install python-click if your distro
  allows it

put into muttrc:
* `macro index,pager E "\et| digest-phabricator-thread.py\n\cT.*\n"`
It will tag current thread, pipe it to script and then untag.
