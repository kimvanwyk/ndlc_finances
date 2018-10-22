from datetime import date
import os, os.path
import shutil
import socket

import build_report
import kppe

UDP_IP = "0.0.0.0"
UDP_PORT = 5001

def build(verbose=True):
    text = build_report.build_markup_file()
    fn = f'{date.today():%y%m%d}_ndlc_finance_report'
    text = kppe.markup(text)
    (ret, retcode) = kppe.build_document(text, os.path.abspath('templates/no_frills_latex.txt'), fn, toc=False)
    if verbose:
        print('Pandoc output:')
        print()
        print(ret)
    if retcode == 0:
        try:
            os.remove(f'/io/{fn}.pdf')
        except Exception as e:
            pass
        shutil.move(f'/app/{fn}.pdf', '/io')
    return (ret, retcode, f'{fn}.pdf')


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM)
    sock.setblocking(1)
    sock.bind((UDP_IP, UDP_PORT))
    rec = []
    while True:
        (data, addr) = sock.recvfrom(1024)
        rec.append(data)
        s = ''.join([str(r) for r in rec])
        if 'build' in s:
            (ret, retcode, fn) = build()
            sock.sendto(bytes(fn, 'utf8') if retcode == 0 else b'error', addr)
            rec = []
        if 'quit' in s:
            break
