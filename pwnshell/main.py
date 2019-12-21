import art
import termcolor
import termios
import atexit
import pty
import os
import tty
import select
import sys
import time

CTRL_S_CHAR = "\x13"
CTRL_Q_CHAR = "\x11"

conf_hex_output = False


def print_welcome():
    art.tprint("pwnshell")
    print "[" + termcolor.colored("!", "green") + "]" + " ctrl+s to enter raw input mode"
    print "[" + termcolor.colored("!", "green") + "]" + " ctrl+c to leave raw input mode"
    print "[" + termcolor.colored("!", "green") + "]" + " ctrl+q to toggle raw output mode between normal and hexdump mode."


def restore_term_attr(backup):
    termios.tcsetattr(0, termios.TCSANOW, backup)
    print "[" + termcolor.colored("-", "red") + "] Bye bye"


def handle_raw_input(pty_fd, backup_term_attr):
    termios.tcsetattr(0, termios.TCSANOW, backup_term_attr)

    try:
        in_buf = raw_input("\n\r[" + termcolor.colored("+", "green") + "] raw input mode:\n\r")
    except KeyboardInterrupt:
        os.write(1, "\r" + termcolor.colored("-", "red") + " normal input mode, changes discarded\n\r")
        tty.setraw(0)
        return

    os.write(sys.stdout.fileno(), "\r[" + termcolor.colored("-", "red") + "] normal input mode\n\r")
    tty.setraw(0)

    #For some reason it only works with sleep
    time.sleep(0.3)

    pty_temp_attr = termios.tcgetattr(pty_fd)
    tty.setraw(pty_fd, termios.TCSANOW)
    os.write(pty_fd, in_buf.decode("string_escape"))

    # For some reason it only works with sleep
    time.sleep(0.3)

    termios.tcsetattr(pty_fd, termios.TCSANOW, pty_temp_attr)


def toggle_hex_output():
    global conf_hex_output

    if conf_hex_output:
        print "\n\r[" + termcolor.colored("-", "red") + "] Leaving hex output mode!\n\r"
    else:
        print "\n\r[" + termcolor.colored("+", "green") + "] entering hex output mode!\n\r"

    conf_hex_output = not conf_hex_output


def pwnshell_recv(pty_fd, backup_term_attr):
    global conf_hex_output

    input_char = os.read(sys.stdin.fileno(), 1)

    if CTRL_S_CHAR == input_char:
        handle_raw_input(pty_fd, backup_term_attr)
    elif CTRL_Q_CHAR == input_char:
        toggle_hex_output()
    else:
        os.write(pty_fd, input_char)


def pwnshell_write(pty_fd, backup_term_attr):
    try:
        output_str = os.read(pty_fd, 0xFFFF)
    except OSError:
        exit()

    if conf_hex_output:
        termios.tcsetattr(0, termios.TCSANOW, backup_term_attr)
        os.system('echo "' + output_str + '" | hexdump -C')
        tty.setraw(0)
    else:
        os.write(sys.stdout.fileno(), output_str)


def main():
    print_welcome()

    backup_term_attr = termios.tcgetattr(0)
    atexit.register(restore_term_attr, backup_term_attr)

    shell_pid, pty_fd = pty.fork()

    assert -1 != shell_pid, "Failed to fork pty!"

    # Execute bash on fork
    if 0 == shell_pid:
        os.execv("/bin/bash", ["bash"])

    tty.setraw(0)

    while True:
        pending_fds = select.select([sys.stdin.fileno(), pty_fd], [], [])

        if pending_fds[0][0] == sys.stdin.fileno():
            pwnshell_recv(pty_fd, backup_term_attr)
        else:
            pwnshell_write(pty_fd, backup_term_attr)

if __name__ == '__main__':
    main()