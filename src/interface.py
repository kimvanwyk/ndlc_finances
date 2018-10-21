from datetime import date
import os, os.path
import socket

import build_report
import kppe

UDP_IP = "0.0.0.0"
UDP_PORT = 5001

def build(verbose=True):
    text = build_report.build_markup_file()
    (ret, retcode) = kppe.build_pdf(text, os.path.abspath('templates/no_frills_latex.txt'), f'{date.today():%y%m%d}_ndlc_finance_report', toc=False)
    if verbose:
        print('Pandoc output:')
        print()
        print(ret)
    return (ret, retcode)

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM)
    sock.setblocking(1)
    sock.bind((UDP_IP, UDP_PORT))
    rec = []
    while True:
        (data, addr) = sock.recvfrom(1024)
        rec.append(data)
        s = ''.join(str(rec))
        if 'build' in s:
            (ret, retcode) = build()
            sock.sendto(b'done' if retcode == 0 else b'error', addr)
            rec = []
        if 'quit' in s:
            break
