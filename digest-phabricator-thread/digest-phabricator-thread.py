#! /usr/bin/env python

import code
import cStringIO
import mailbox
import os
import quopri
import sys

from email.utils import parsedate
from tempfile import NamedTemporaryFile

import click


class MyMail(object):
    pass


def filter_stuff(body):
    # filter away 'EMAIL PREFERENCES', 'TASK DETAILS' and 'To:', 'From:' stuff
    # out of phab email
    out = []
    skip_lines = 0
    for line in body.split('\n'):
        if skip_lines > 0:
            skip_lines -= 1
            continue
        if line.startswith('EMAIL PREFERENCES'):
            skip_lines = 2
            continue
        elif line.startswith('TASK DETAIL'):
            skip_lines = 2
            continue
        elif line.startswith('To: '):
            continue
        elif line.startswith('Cc: '):
            continue
        out.append(line)
    return '\n'.join(out)


def maybe_decode(content_transfer_encoding, data):
    if content_transfer_encoding == 'quoted-printable':
        output_f = cStringIO.StringIO()
        input_f = cStringIO.StringIO(data)
        # maybe email.quopriMIME?
        quopri.decode(input_f, output_f)
        input_f.close()
        # f.ck output_f close, cStringIO doesn't work with `with`
        output_f.seek(0)
        return output_f.read()
    return data


@click.command()
@click.option('-i', '--input-file', default='-',
              help='Input file with list of emails [stdin]', type=str)
@click.option('-o', '--output-file', default='-',
              help='Output file to show [stdout]', type=str)
@click.option('-d', '--debug', is_flag=True,
              help='Run interactive interpreter in the middle')
def main(input_file, output_file, debug):
    if input_file == '-':
        if debug:
            raise BaseException("cannot run --debug with stdin input")
        input_file = sys.stdin
    else:
        input_file = open(input_file)

    # store / filter input
    tmpf = NamedTemporaryFile()
    # created digest
    output = NamedTemporaryFile()

    # mailbox needs filename :( that's breaking duck typing!
    # with below From hack I could probably split msgs myself altogether
    for line in input_file:
        # mutt pipe-to doesn't do mbox format :( this will break soon :)
        if line.startswith('Delivered-To: '):
            tmpf.write('From ABC@DEF.XYZ Thu Aug 15 16:24:28 2019\n')
        tmpf.write(line)
    tmpf.flush()
    tmpf.seek(0)

    mbox = mailbox.mbox(tmpf.name)
    # transform headers to dict, lowercase and merge multiline headers, decode
    # quoted-printable bodies
    mbox_usable = []
    for msg in mbox:
        mbox_usable.append(MyMail())
        mbox_usable[-1].headers = dict([(h.lower(), v.replace('\n', ' '))
                                        for (h, v) in msg._headers])
        mbox_usable[-1].body = maybe_decode(
            mbox_usable[-1].headers['content-transfer-encoding'],
            msg.get_payload())

    mbox_usable.sort(key=lambda x: parsedate(x.headers['date']))

    if debug:
        code.interact(local=locals())

    first = True
    for msg in mbox_usable:
        if first is True:
            print >>output, '>____________________________________________________________________<'
            print >>output, 'Date: ', msg.headers.get('date')
            print >>output, 'Subject: ', msg.headers.get('subject')
            print >>output
            print >>output, msg.body
            first = False
        else:
            print >>output, '>____________________________________________________________________<'
            print >>output, 'Date: ', msg.headers.get('date')
            print >>output, filter_stuff(msg.body)

    output.flush()
    tmpf.close()

    os.system("vim -c 'set ft=mail' -c 'set wrap' '%s'" % output.name)


if __name__ == '__main__':
    main()

