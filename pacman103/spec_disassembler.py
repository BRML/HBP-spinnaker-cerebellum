"""Data Spec Disassembler

Run with -h for command-line arguments.

Andrew Mundy
University of Manchester 2014
"""

import argparse
import inspect
import numpy as np
import sys

from pacman103.lib import data_spec_constants
from pacman103.core import exceptions


opstrings = dict(map(
    lambda m: (m[0][4:], m[1]),
    filter(
        lambda m: m[0][0:4] == "DSG_",
        inspect.getmembers(data_spec_constants)
    )
))


def disassemble(opstring):
    def f_(f):
        f._opcode = opstrings[opstring]
        f._opstring = opstring
        return f
    return f_


class SpecDisassembler(object):
    """A callable class which reads in a given data spec file when called and
    writes out a disassembled spec.
    """
    def __init__(self):
        # Generate the dictionary of opcodes that are implemented
        fs = filter(
            lambda f: hasattr(f[1], '_opcode'),
            inspect.getmembers(self, inspect.ismethod)
        )
        self._ops = dict([(f[1]._opcode, f[1]) for f in fs])

    def __call__(self, f_in, f_out):
        """Read the given file, execute the spec it contains and write the
        result out to the given file.
        """
        # Open the command stream for reading
        self.spec_file = f_in
        self.spec_strm = np.fromfile(f_in, dtype='uint32')
        self.spec_len = self.spec_strm.size

        # Open the spec disassemble file for writing
        self.f_out = f_out

        # Write the header
        self._write_header()

        # Initialise registers
        # "System" Registers
        self.program_counter = 8
        self.program_counter_next = 0x0
        self.halt = False
        self.cmd_len = 0x0
        self.opcode = 0x0
        self.use_dest_reg = False
        self.use_src1_reg = False
        self.use_src2_reg = False
        self.dest_reg = 0x0
        self.src1_reg = 0x0
        self.src2_reg = 0x0

        while not self.halt and self.program_counter < self.spec_len:
            # Fetch
            cmd = self.spec_strm[self.program_counter]

            # Decode
            self.opcode = (cmd >> 20) & 0xFF
            self.use_dest_reg = (cmd >> 18) & 0x1 == 0x1
            self.use_src1_reg = (cmd >> 17) & 0x1 == 0x1
            self.use_src2_reg = (cmd >> 16) & 0x1 == 0x1
            self.dest_reg = (cmd >> 12) & 0xF
            self.src1_reg = (cmd >> 8) & 0xF
            self.src2_reg = (cmd >> 4) & 0xF
            self.cmd = cmd

            self.cmd_len = self._command_length(
                cmd, self.opcode, self.spec_strm[self.program_counter+1]
            )
            self.program_counter_next = self.cmd_len + self.program_counter + 1

            # Execute
            try:
                f = self._ops[self.opcode]
                s = f()
                self._write_command(
                    "%s: %s" % (f._opstring, s if s is not None else "")
                )
            except KeyError:
                raise exceptions.SpecExecCmdException(
                    "Unrecognised opcode %#04x" % self.opcode
                )

            # Increment program counter
            self.program_counter = self.program_counter_next

    def _write_command(self, comment):
        self.f_out.write("%# 10x %s\n" % (self.program_counter, comment))

    def _write_header(self):
        """Write information from the header of the spec file.
        """
        self.f_out.write("#" * 79)
        self.f_out.write("\nDisassembly of %s\n" % self.spec_file)

        self.f_out.write("SPEC VERSION:\t%#x\n" % self.spec_strm[1])
        self.f_out.write("MACHINE TIMESTEP:\t%d\n" % self.spec_strm[5])

        self.f_out.write("#" * 79)
        self.f_out.write("\n\n")

    @disassemble("NOP")
    def _nop(self):
        pass

    @disassemble("RESERVE")
    def _reserve(self):
        # Extract elements from the command
        slot = self.cmd & 0x1F  # cmd[4:0]
        size = self.spec_strm[self.program_counter + 1]
        unfilled = (self.cmd >> 7) & 0x1 == 0x1

        return "Slot = %d, Size = %d (bytes) %s" % (
            slot, size, "UNFILLED" if unfilled else "FILLED"
        )

    @disassemble("SWITCH_FOCUS")
    def _switch_focus(self):
        """Switch the current memory focus.
        """
        if not self.use_src1_reg:
            region = (self.cmd >> 8) & 0xF
            return "Region = %d" % region
        else:
            return "Region = [%d]" % self.src1_reg

    @disassemble("WRITE")
    def _write(self):
        # Get number of repeats
        n_repeats = 1
        if self.use_src2_reg:
            n_repeats = "[%s]" % self.src2_reg
        else:
            n_repeats = "%s" % (self.cmd & 0xFF)

        # Get the data value and data size
        value = 0x00000000
        if self.use_src1_reg:
            value = "[%d]" % self.src1_reg
        else:
            value = "%#010x" % self.spec_strm[self.program_counter + 1]
        data_len = 2 ** ((self.cmd >> 12) & 0x3)  # 2 bit field for length

        # Perform the writes
        return "Size = %d (bytes), repeats = %s, value = %s" % (
            data_len, n_repeats, value
        )

    @disassemble("WRITE_ARRAY")
    def _write_array(self):
        """Write a block of binary words data to memory.
        """
        length = self.spec_strm[self.program_counter + 1] - 1

        comment = "%d words:\n" % length
        for (i, v) in enumerate(self.spec_strm[
                self.program_counter+2:self.program_counter+length+2]):
            comment += "\t\t\t\t\t[%4d] = %#010x\n" % (i, v)
        return comment[:-1]

    @disassemble("LOOP")
    def _start_loop(self):
        """Start a loop.

        Add a new loop to the stack and change the necessary registers.
        """
        i = 1
        reg = self.cmd & 0xF
        if self.use_dest_reg:
            start = "[%d]" % self.dest_reg
        else:
            start = "%d" % self.spec_strm[self.program_counter + i]
            i += 1

        if self.use_src1_reg:
            end = "[%d]" % self.src1_reg
        else:
            end = "%d" % self.spec_strm[self.program_counter + i]
            i += 1

        if self.use_src2_reg:
            inc = "[%d]" % self.src2_reg
        else:
            inc = "%d" % self.spec_strm[self.program_counter + i]

        return "FROM %d to %d striding %d USING [%d]" % (start, end, inc, reg)

    @disassemble("BREAK_LOOP")
    def _break_loop(self):
        pass

    @disassemble("END_LOOP")
    def _end_loop(self):
        pass

    @disassemble("MV")
    def _move_to_register(self):
        if not self.use_dest_reg:
            return "No destination register"

        if self.use_src1_reg:
            return "[%d] := [%d]" % (self.dest_reg, self.reg1_src)
        else:
            return "[%d] := %# 10x" % (
                self.dest_reg, self.spec_strm[self.program_counter+1]
            )

    @disassemble("SET_WR_PTR")
    def _set_write_pointer(self):
        relative = False
        if self.cmd & 0x1 == 1:
            relative = True

        new_ptr = self.spec_strm[self.program_counter+1]
        if self.use_src1_reg:
            new_ptr = self.reg[self.reg1_src]

        if relative:
            new_ptr += ((self.current_memory.wr_ptr_aligned << 2) +
                        self.current_memory.wr_ptr_offset)

        aligned = new_ptr >> 2
        offset = new_ptr & 0x3
        return "%# 10x: Aligned = %# 10x, offset = %d" % (
            new_ptr, aligned, offset
        )

    @disassemble("END_SPEC")
    def _end_spec(self):
        # TODO: Ensure that we are not in constructor blocks, etc.
        self.halt = True

    def _command_length(self, cmd, opcode, nextword):
        """Get the length of given command (and opcode)

        This is included to avoid duplication of this code.
        """
        if opcode == data_spec_constants.DSG_END_SPEC:
            return -1

        cmd_len = (cmd >> 28) & 0xF

        if cmd_len == 0xF:
            cmd_len = nextword

        return cmd_len

if __name__ == "__main__":
    # Run the disassembler on the given files
    parser = argparse.ArgumentParser()
    parser.add_argument("spec_file", help="the file to disassemble")
    parser.add_argument(
        "out_file", nargs="?", help="output file (stdout by default)",
        default=sys.stdout
    )

    args = parser.parse_args()

    f_in = args.spec_file
    f_out = args.out_file

    if f_out != sys.stdout:
        f_out = open(args.out_file, 'w+')

    # Create the disassembler and run
    sde = SpecDisassembler()
    sde(f_in, f_out)

    if f_out != sys.stdout:
        f_out.close()
