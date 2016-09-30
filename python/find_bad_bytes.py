# find non-ascii characters, e.g. stylized apostrophes
#
# http://stackoverflow.com/questions/21639275/python-syntaxerror-non-ascii-character-xe2-in-file


file = "OpenNfuMain.py"

with open(file) as fp:
    for i, line in enumerate(fp):
        if "\xe2" in line:
            print i, repr(line)

