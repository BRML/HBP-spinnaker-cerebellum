"""Data Spec Executor
"""

import inspect
import logging
import numpy as np

from pacman103.lib import data_spec_constants
from pacman103.core import exceptions

logger = logging.getLogger(__name__)


class LoopContext(object):
    def __init__(self, start_addr, start_val, end_val, inc, reg):
        self.start_addr = start_addr
        self.end_addr = None
        self.start_val = start_val
        self.end_val = end_val
        self.inc = inc
        self.reg = reg


class LoopStack(object):
    """A stack of LoopContext elements."""
    def __init__(self):
        self._contexts = []

    def pop(self):
        self._contexts.pop()

    def push(self, start_addr, start_val, end_val, inc, reg):
        """Add a new Context to the stack."""
        self._contexts.append(LoopContext(
            start_addr, start_val, end_val, inc, reg
        ))

    @property
    def current_loop(self):
        try:
            return self._contexts[-1]
        except KeyError:
            raise Exception("Not currently in a loop.")

class Chip(object):
    """A chip, to keep track of SDRAM usage
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.sdram_used = 0
        self.memory_map = list()

class MemorySlotCollection(object):
    """Collection of memory slots.
    """
    def __init__(self, n_slots):
        """Create a new MemorySlotCollection with the given number of slots.
        """
        self._n_slots = n_slots
        self._slots = [None] * n_slots

    def __len__(self):
        return self._n_slots

    def __getitem__(self, key):
        return self._slots[key]

    def __setitem__(self, key, value):
        if self._slots[key] is not None:
            raise KeyError(key)

        self._slots[key] = value

    def __iter__(self):
        return iter(self._slots)

    @property
    def regions(self):
        for slot in self._slots:
            yield slot

    @property
    def _utilised_regions(self):
        for i in range(0, self._n_slots):
            if self._slots[i] is not None and self._slots[i].size > 0:
                if self._slots[i].unfilled == False:
                    logger.debug("1. Returning slot {} {}".format(i, self._slots[i].__repr__()))
                    yield self._slots[i]
                else:
                    is_next_slot = False
                    logger.debug("Deciding whether to return slot {}".format(i))
                    for j in range(i + 1, self._n_slots):
                        if self._slots[j] is not None and self._slots[j].unfilled == False and self._slots[j].size > 0:
                            logger.debug("Found slot {} after {} which is used: {}".format(i, j, self._slots[j].__repr__()))
                            is_next_slot = True
                            break
                    if is_next_slot == True:
                        logger.debug("2. Returning slot {} {}".format(i, self._slots[i].__repr__()))
                        yield self._slots[i]

    def tofile(self, filename):
        """Write the memory slots to the given file."""
        # Construct the complete matrix, write to the given filename
        m = np.hstack([r.memory for r in self._utilised_regions])
        m.tofile(filename)


class MemorySlot(object):
    """Memory slot controls access to a block of memory.
    """
    def __init__(self, size, unfilled=False):
        """Create a new memory slot with the given size.  If unfilled is true
        then the region is not written to file.
        """
        # Write pointers
        self.wr_ptr_aligned = 0x0
        self.wr_ptr_offset = 0x0

        self.unfilled = unfilled

        # The actual block of memory
        self.size = size
        self.memory = np.zeros(size, dtype='uint32')

    @property
    def write_pointer(self):
        """Get the current write pointer position in bytes."""
        return 4 * self.wr_ptr_aligned + self.wr_ptr_offset

    def __repr__(self):
        return "MemorySlot <Size = %d, Aligned = %#010x, Offset = %#x, %s>" % (
            self.size, self.wr_ptr_aligned, self.wr_ptr_offset,
            "UNFILLED" if self.unfilled else "FILLED"
        )


opstrings = dict(map(
    lambda m: (m[0][4:], m[1]),
    filter(
        lambda m: m[0][0:4] == "DSG_",
        inspect.getmembers(data_spec_constants)
    )
))


def implements(opstring):
    """Mark a function as being the function to execute for the given
    opcode.
    """
    def f_(f):
        f._opstring = opstring
        f._opcode = opstrings[opstring]
        return f
    return f_


class SpecExecutor(object):
    """A callable class which reads in a given data spec file when called and
    writes out an executed spec.
    """
    
    def __init__(self):
        # Generate the dictionary of opcodes that are implemented
        fs = filter(
            lambda f: hasattr(f[1], '_opcode'),
            inspect.getmembers(self, inspect.ismethod)
        )
        self._ops = dict([(f[1]._opcode, f[1]) for f in fs])

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

    def __call__(self, f_in, f_out, chip):
        """Read the given file, execute the spec it contains and write the
        result out to the given file.  Ensure that memory usage is correct
        given the input processor.
        """
        # Open the command stream for reading
        self.spec_file = f_in
        self.spec_strm = np.fromfile(f_in, dtype='uint32')
        self.spec_len = self.spec_strm.size

        # Check the header
        self._check_header()

        # Initialise general state
        self.timer_period = self.spec_strm[5]
        self.chip = chip

        self.memory_slots = MemorySlotCollection(
            data_spec_constants.MAX_MEM_REGIONS
        )
        self.current_memory = None
        self.reserve_memory_region(
            0, data_spec_constants.APP_PTR_TABLE_BYTES_SZ
        )

        self.loop_stack = LoopStack()

        self.structs = [None] * data_spec_constants.MAX_STRUCT_SLOTS
        self.current_struct = None

        self.constructors = [None] * data_spec_constants.MAX_CONSTRUCTORS
        self.current_constructor = None

        self.rngs = [None] * data_spec_constants.MAX_RNGS
        self.current_rng = None

        self.random_distributions = \
            [None] * data_spec_constants.MAX_RANDOM_DISTS
        self.current_random_distribution = None

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

        # Data Registers
        self.reg = [0] * data_spec_constants.MAX_REGISTERS

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
                cmd, self.opcode, self.program_counter
            )
            self.program_counter_next = self.cmd_len + self.program_counter + 1

            # Execute
            try:
                self._ops[self.opcode]()
            except KeyError:
                raise exceptions.SpecExecCmdException(
                    "Unrecognised opcode %#04x" % self.opcode
                )
            except Exception:
                try:
                    raise
                finally:
                    print("SPEC FILE: %s" % f_in)
                    print("PROGRAM COUNTER:\t%#010x" % self.program_counter)
                    print("COMMAND WORD:\t%#010x" % self.cmd)
                    print("OPCODE:\t\t\t%#04x (%s)" % (
                        self.opcode, self._ops[self.opcode]._opstring
                    ))
                    print("Memory Slot Status:")
                    print(self.memory_slots)

            # Increment program counter
            self.program_counter = self.program_counter_next

        # Write the application pointer table, write to file
        self._write_app_ptr_table()
        self.memory_slots.tofile(f_out)
        
    def setup(self, chip):
        self.chip = chip
        self.memory_slots = MemorySlotCollection(
            data_spec_constants.MAX_MEM_REGIONS
        )
        self.current_memory = None
        self.reserve_memory_region(
            0, data_spec_constants.APP_PTR_TABLE_BYTES_SZ
        )

        self.loop_stack = LoopStack()

        self.structs = [None] * data_spec_constants.MAX_STRUCT_SLOTS
        self.current_struct = None

        self.constructors = [None] * data_spec_constants.MAX_CONSTRUCTORS
        self.current_constructor = None

        self.rngs = [None] * data_spec_constants.MAX_RNGS
        self.current_rng = None

        self.random_distributions = \
            [None] * data_spec_constants.MAX_RANDOM_DISTS
        self.current_random_distribution = None
        
        # Data Registers
        self.reg = [0] * data_spec_constants.MAX_REGISTERS
        
    def finish(self, f_out):
        self._write_app_ptr_table()
        self.memory_slots.tofile(f_out)
        
    def call(self, cmd_word_list):
        self.spec_strm = cmd_word_list
        self.program_counter = 0
        self.program_counter_next = 0x0
        self.halt = False
        
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
            cmd, self.opcode, self.program_counter
        )
        self.program_counter_next = self.cmd_len + self.program_counter + 1

        # Execute
        try:
            self._ops[self.opcode]()
        except KeyError:
            raise exceptions.SpecExecCmdException(
                "Unrecognised opcode %#04x" % self.opcode
            )
        except Exception:
            try:
                raise
            finally:
                print("PROGRAM COUNTER:\t%#010x" % self.program_counter)
                print("COMMAND WORD:\t%#010x" % self.cmd)
                print("OPCODE:\t\t\t%#04x (%s)" % (
                    self.opcode, self._ops[self.opcode]._opstring
                ))
                print("Memory Slot Status:")
                print(self.memory_slots)

        # Increment program counter
        self.program_counter = self.program_counter_next

    def _check_header(self):
        """Ensure that values within the first 8 words are as expected.
        """
        if not self.spec_strm[0] == data_spec_constants.DSG_MAGIC_NUM:
            raise exceptions.MalformedHeaderException(
                "Header of file '%s' does not conform to a valid Data Spec."
                % self.spec_file
            )

        expected_dsg = (data_spec_constants.DSG_LIB_VER_MAJ << 16) + \
            data_spec_constants.DSG_LIB_VER_MIN
        if not self.spec_strm[1] == expected_dsg:
            logger.warn(
                "DSG library version number given in file '%s' does not match "
                "version expected by this parser.  Continuing anyway..."
                % self.spec_file
            )

        if self.spec_strm[5] < 100:
            logger.warn("Timer tick period is less that 100 us.")
            
    def write_header(self, header_data):
        if not header_data[0] == data_spec_constants.DSG_MAGIC_NUM:
            raise exceptions.MalformedHeaderException(
                "Header does not conform to a valid Data Spec."
            )

        expected_dsg = (data_spec_constants.DSG_LIB_VER_MAJ << 16) + \
            data_spec_constants.DSG_LIB_VER_MIN
        if not header_data[1] == expected_dsg:
            logger.warn(
                "DSG library version number does not match "
                "version expected by this parser.  Continuing anyway..."
            )

        if header_data[5] < 100:
            logger.warn("Timer tick period is less that 100 us.")
        
        self.timer_period = header_data[5]

    def _write_app_ptr_table(self):
        """Write the header info followed by the Application Pointer Table.
        """
        header = self.memory_slots[0].memory
        header[0] = data_spec_constants.APPDATA_MAGIC_NUM
        header[1] = 0x00010000  # Version 1.0
        header[2] = self.timer_period
        header[3] = 0x00000000  # Reserved

        # TODO: Investigate use of reduce here
        start_blk = 0
        for (i, slot) in enumerate(self.memory_slots.regions):
            if slot is not None:
                header[4+i] = start_blk
                start_blk += slot.size * 4

    @implements("NOP")
    def _nop(self):
        pass

    @implements("RESERVE")
    def _reserve(self):
        """Reserve a block of memory in SDRAM.  In this host based model
        memory is simply allocated sequentially until it's used up.
        """
        # Extract elements from the command
        slot = self.cmd & 0x1F  # cmd[4:0]
        size = self.spec_strm[self.program_counter + 1]
        unfilled = (self.cmd >> 7) & 0x1 == 0x1

        if size == 0:
            raise exceptions.SpecExecCmdException(
                "Region of size zero requested - unsupported."
            )

        if size & 0x3 != 0:
            size = (size + 4) - (size & 0x3)

        self.reserve_memory_region(slot, size, unfilled)

    def reserve_memory_region(self, slot, size=0, unfilled=False):
        size_words = size / 4

        # Ensure that we have enough memory left
        start_addr = self.chip.sdram_used
        if start_addr & 0x3 != 0:
            raise Exception("Unaligned start address.")

        end_addr = start_addr + size - 1

        if (end_addr > data_spec_constants.ROUTING_TABLE_ADDRESS and
                end_addr > data_spec_constants.CORE_MAP_ADDRESS):
            raise exceptions.SpecExecCmdException(
                "Requested memory region %d is extends beyond allowable range."
                % slot
            )

        for (i, mem) in enumerate(self.chip.memory_map):
            if ((start_addr >= mem[0] and start_addr <= mem[1]) or
                    (end_addr >= mem[0] and end_addr <= mem[1])):
                raise exceptions.SpecExecCmdException(
                    "Requested memory region %d clashes with existing memory "
                    "region %d. (Requested %d to %d, clashes with %d to %d"
                    ")" % (slot, i, start_addr, end_addr, mem[0], mem[1])
                )

        self.memory_slots[slot] = MemorySlot(size_words, unfilled=unfilled)

        # Add reserved memory array to the list
        # TODO: If this is not used elsewhere, then replace with a named
        #   tuple or something to make it more readable!
        self.chip.memory_map.append([start_addr, end_addr])
        self.chip.sdram_used = end_addr + 1

    @implements("SWITCH_FOCUS")
    def _switch_focus(self):
        """Switch the current memory focus.
        """
        region = self.reg[self.src1_reg]
        if not self.use_src1_reg:
            region = (self.cmd >> 8) & 0xF

        if self.memory_slots[region] is None:
            raise Exception(
                "Switching focus to unreserved memory region [%d]." % region
            )

        self.current_memory = self.memory_slots[region]

    @implements("WRITE")
    def _write(self):
        """Perform a single or repeated block of writes to the current open
        memory region.
        """
        # Get number of repeats
        n_repeats = 1
        if self.use_src2_reg:
            n_repeats = self.reg[self.src2_reg]
        else:
            n_repeats = self.cmd & 0xFF

        # Get the data value and data size
        value = 0x00000000
        if self.use_src1_reg:
            value = self.reg[self.src1_reg]
        else:
            value = self.spec_strm[self.program_counter + 1]
        data_len = 2 ** ((self.cmd >> 12) & 0x3)  # 2 bit field for length

        # Perform the writes
        self._write_to_mem_array(
            value=value, n_bytes=data_len, repeat=n_repeats
        )

    @implements("WRITE_ARRAY")
    def _write_array(self):
        """Write a block of binary words data to memory.
        """
        if self.current_memory.wr_ptr_offset != 0:
            raise Exception("Not aligned to word boundary before WRITE_ARRAY.")

        # Get the length and aligned write pointer
        aligned = self.current_memory.wr_ptr_aligned
        length = self.spec_strm[self.program_counter + 1] - 1

        # Perform the copy
        self.current_memory.memory[aligned:aligned + length] = self.spec_strm[
            self.program_counter+2:self.program_counter+length+2
        ]

        # Write back the aligned pointer
        self.current_memory.wr_ptr_aligned += length

    @implements("LOOP")
    def _start_loop(self):
        """Start a loop.

        Add a new loop to the stack and change the necessary registers.
        """
        i = 1
        reg = self.cmd & 0xF
        if self.use_dest_reg:
            start = self.reg[self.dest_reg]
        else:
            start = self.spec_strm[self.program_counter + i]
            i += 1

        if self.use_src1_reg:
            end = self.reg[self.src1_reg]
        else:
            end = self.spec_strm[self.program_counter + i]
            i += 1

        if self.use_src2_reg:
            inc = self.reg[self.src2_reg]
        else:
            inc = self.spec_strm[self.program_counter + i]

        self.loop_stack.push(self.program_counter_next, start, end, inc, reg)
        self.reg[reg] = start

    @implements("BREAK_LOOP")
    def _break_loop(self):
        """Break out of a loop.
        """
        current_loop = self.loop_stack.current_loop

        # Search for the end of the loop if necessary
        if current_loop.end_addr is None:
            _program_counter = self.program_counter_next

            while _program_counter < self.spec_len:
                cmd = self.spec_strm[_program_counter]
                opcode = (cmd >> 20) & 0xFF
                open_loops = 1

                if opcode == data_spec_constants.DSG_LOOP:
                    open_loops += 1

                elif opcode == data_spec_constants.DSG_END_LOOP:
                    open_loops -= 1

                _program_counter += self._command_length(
                    cmd, opcode, _program_counter
                )

                if open_loops == 0:
                    current_loop.end_addr = _program_counter
                    break

        if current_loop.end_addr is None:
            raise exceptions.SpecExecCmdException(
                "BREAK_LOOP:Cannot find end of loop."
            )

        self.loop_stack.pop()
        self.program_counter_next = current_loop.end_addr

    @implements("END_LOOP")
    def _end_loop(self):
        """End of a loop.
        """
        loop = self.loop_stack.current_loop

        if loop.end_addr is None:
            loop.end_addr = self.program_counter_next

        # Increment the loop counter, test and jump if necessary
        self.reg[loop.reg] += loop.inc
        if self.reg[loop.reg] < loop.end_val:
            self.program_counter_next = loop.start_addr
        else:
            self.loop_stack.pop()

    @implements("MV")
    def _move_to_register(self):
        if not self.use_dest_reg:
            raise exceptions.SpecExecCmdException("MV:No destination register")

        if self.use_src1_reg:
            self.reg[self.dest_reg] = self.reg[self.reg1_src]
        else:
            self.reg[self.dest_reg] = self.spec_strm[self.program_counter+1]

    @implements("SET_WR_PTR")
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

        self.current_memory.wr_ptr_aligned = new_ptr >> 2
        self.current_memory.wr_ptr_offset = new_ptr & 0x3

    @implements("END_SPEC")
    def _end_spec(self):
        # TODO: Ensure that we are not in constructor blocks, etc.
        self.halt = True

    def _command_length(self, cmd, opcode, program_counter):
        """Get the length of given command (and opcode)

        This is included to avoid duplication of this code.
        """
        if opcode == data_spec_constants.DSG_END_SPEC:
            return -1

        cmd_len = (cmd >> 28) & 0xF

        if cmd_len == 0xF:
            cmd_len = self.spec_strm[program_counter+1]

        return cmd_len

    def _write_to_mem_array(self, value, n_bytes, memory_slot=None,
                            aligned=None, offset=None, repeat=1):
        """Write to a memory array.

        If a memory slot is not assigned the current memory slot is used.
        Likewise, if neither the aligned or offset pointers are provided the
        next free space in memory is used.

        The resultant pointers are returned and may need writing back to the
        memory slot.
        """
        # Get parameters
        if memory_slot is None:
            memory_slot = self.current_memory

        if aligned is None:
            aligned = memory_slot.wr_ptr_aligned

        if offset is None:
            offset = memory_slot.wr_ptr_offset

        # Perform the write
        for r in range(repeat):
            if n_bytes == 4:
                self._write_word_to_mem_array(
                    value, memory_slot, aligned, offset
                )
            elif n_bytes == 2:
                self._write_half_word_to_mem_array(
                    value, memory_slot, aligned, offset
                )
            elif n_bytes == 1:
                self._write_byte_to_mem_array(
                    value, memory_slot, aligned, offset
                )

            # Calculate the new pointers
            _offset = offset
            offset = (offset + n_bytes) & 0x3
            aligned = aligned + (1 if offset <= _offset else 0)

        # Write back
        memory_slot.wr_ptr_offset = offset
        memory_slot.wr_ptr_aligned = aligned

    def _write_byte_to_mem_array(self, value, mem, aligned, offset):
        """Write a single byte to a memory array.
        """
        offset *= 8                # Convert to bits
        mask = 0xFF << offset      # Mask for input value
        mask_ = 0xFFFFFFFF ^ mask  # Mask for extant values
        value <<= offset           # Shift the value as well

        # Modify the value in the given memory
        try:
            mem.memory[aligned] = (mem.memory[aligned] & mask_) | \
                (value & mask)
        except IndexError as e:
            raise exceptions.SpecExecCmdException(
                "Cannot write to word %d of memory slot of size %d." %
                (aligned, mem.size)
            )

    def _write_half_word_to_mem_array(self, value, mem, aligned, offset):
        """Write 2 bytes to a memory array.
        """
        if offset < 3:
            offset *= 8                # Convert to bits
            mask = 0xFFFF << offset    # Mask for input value
            mask_ = 0xFFFFFFFF ^ mask  # Mask for extant values
            value <<= offset           # Shift the value

            try:
                mem.memory[aligned] = ((mem.memory[aligned] & mask_) |
                                       (value & mask))
            except IndexError as e:
                raise exceptions.SpecExecCmdException(
                    "Cannot write to word %d of memory slot of size %d." %
                    (aligned, mem.size)
                )
        else:
            # Byte | Byte
            self._write_byte_to_mem_array(
                value & 0x00FF, mem, aligned, offset
            )
            self._write_byte_to_mem_array(
                (value & 0xFF00) >> 8, mem, aligned + 1, 0
            )

    def _write_word_to_mem_array(self, value, mem, aligned, offset):
        """Write 4 bytes to a memory array.
        """
        if offset == 0:
            try:
                mem.memory[aligned] = value & 0xFFFFFFFF
            except IndexError as e:
                raise exceptions.SpecExecCmdException(
                    "Cannot write to word %d of memory slot of size %d." %
                    (aligned, mem.size)
                )
        elif offset == 2:
            # Half Word | Half Word
            self._write_half_word_to_mem_array(
                value & 0x0000FFFF, mem, aligned, offset
            )
            self._write_half_word_to_mem_array(
                (value & 0xFFFF0000) >> 16, mem, aligned + 1, 0
            )
        elif offset == 1:
            # Byte, Half Word | Byte
            self._write_byte_to_mem_array(
                value & 0x000000FF, mem, aligned, offset
            )
            self._write_half_word_to_mem_array(
                (value & 0x00FFFF00) >> 8, mem, aligned, offset + 1
            )
            self._write_byte_to_mem_array(
                (value & 0xFF000000) >> 24, mem, aligned + 1, 0
            )
        elif offset == 3:
            # Byte | Half Word, Byte
            self._write_byte_to_mem_array(
                value & 0x000000FF, mem, aligned, offset
            )
            self._write_half_word_to_mem_array(
                (value & 0x00FFFF00) >> 8, mem, aligned + 1, 0
            )
            self._write_byte_to_mem_array(
                (value & 0xFF000000) >> 24, mem, aligned + 1, 2
            )
