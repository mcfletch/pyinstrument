from optparse import OptionParser
import sys
import os
import codecs
from pyinstrument import Profiler

def write_output( options, profiler ):
    try:
        if options.outfile:
            f = codecs.open(options.outfile, 'w', 'utf-8')
            unicode = True
            color = False
        else:
            f = sys.stdout
            unicode = stdout_supports_unicode()
            color = stdout_supports_color()

        if options.output_json:
            f.write(profiler.as_json())
        elif options.output_html:
            f.write(profiler.output_html())
        else:
            f.write(profiler.output_text(unicode=unicode, color=color))
    finally:
        if f is not sys.stdout:
            f.close()
    

def main():
    usage = "usage: %prog [-h] [[-o output_file_path] scriptfile [arg] ...] | [ -i infile ]"
    parser = OptionParser(usage=usage)
    parser.allow_interspersed_args = False
    parser.add_option('', '--html',
        dest="output_html", action='store_true',
        help="output HTML instead of text", default=False)
    parser.add_option('', '--json',
        dest="output_json", action='store_true',
        help="output raw JSON dump instead of text or HTML", default=False)
    parser.add_option('-o', '--outfile',
        dest="outfile", action='store', 
        help="save stats to <outfile>", default=None)
    parser.add_option('-i', '--infile',
        dest="infile", action='store', 
        help="load stats from JSON file <infile>", default=None)

    if not sys.argv[1:]:
        parser.print_usage()
        sys.exit(2)

    (options, args) = parser.parse_args()
    sys.argv[:] = args

    if len(args) > 0:
        progname = args[0]
        sys.path.insert(0, os.path.dirname(progname))

        with open(progname, 'rb') as fp:
            code = compile(fp.read(), progname, 'exec')
        globs = {
            '__file__': progname,
            '__name__': '__main__',
            '__package__': None,
        }

        profiler = Profiler()
        profiler.start()

        try:
            exec code in globs, None
        except SystemExit, KeyboardInterrupt:
            pass

        profiler.stop()
        
        write_output( options, profiler )

    elif options.infile:
        profiler = Profiler()
        if options.infile in (b'-','-'):
            fh = sys.stdin
        else:
            fh = codecs.open( options.infile, 'r', 'utf-8')
        try:
            content = fh.read()
        finally:
            fh.close()
        
        profiler.from_json( content )
        write_output( options, profiler )
        
    else:
        parser.print_usage()
    return parser

def stdout_supports_color():
    """
    Returns True if the running system's terminal supports color, and False
    otherwise.

    Borrowed from Django
    https://github.com/django/django/blob/master/django/core/management/color.py
    """
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                  'ANSICON' in os.environ)

    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if not supported_platform or not is_a_tty:
        return False
    return True

def stdout_supports_unicode():
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    utf_in_locale = 'utf' in os.environ.get('LC_CTYPE', '').lower()

    return is_a_tty and utf_in_locale

if __name__ == '__main__':
    main()
