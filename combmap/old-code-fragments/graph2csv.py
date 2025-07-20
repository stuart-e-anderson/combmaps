#!/usr/bin/env python3
import sys
for fname in sys.argv[1:]:
    with open(fname, 'r') as infile:
        print('Source,Target,Type')
        adj = infile.readline().strip().split(',')
        for (st, to) in enumerate(adj):
            for end in to:
                en = ord(end)-ord('a')
                if st < en:
                    print(st, en, 'Undirected', sep=',')

if len(sys.argv) == 1:
    print('Source,Target,Type')
    adj = input().strip().split(',')
    for (st, to) in enumerate(adj):
        for end in to:
            en = ord(end)-ord('a')
            if st < en:
                print(st, en, 'Undirected', sep=',')
