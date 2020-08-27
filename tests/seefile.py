import sys
from pstats import Stats

my_stat = Stats('d:\\d\POST.root.108ms.1590333310.prof', stream=sys.stdout)
my_stat.print_stats()