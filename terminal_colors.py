def print_color(color, *args, **kwargs):
    print(color, *args, TC_FG_ENDC, **kwargs)

TC_FG_BRIGHT_RED     = '\033[91m'
TC_FG_BRIGHT_GREEN   = '\033[92m'
TC_FG_BRIGHT_YELLOW  = '\033[93m'
TC_FG_BRIGHT_BLUE    = '\033[94m'
TC_FG_BRIGHT_MAGENTA = '\033[95m'
TC_FG_BRIGHT_CYAN    = '\033[96m'

TC_FG_BLUE    = '\033[34m'
TC_FG_MAGENTA = '\033[35m'

TC_FG_ENDC = '\033[0m'

TC_ST_BOLD      = '\033[1m'
TC_ST_UNDERLINE = '\033[4m'