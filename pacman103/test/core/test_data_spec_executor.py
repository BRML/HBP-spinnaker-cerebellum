import operator
import pytest

from pacman103.core import data_spec_executor as dse


@pytest.fixture()
def specexec_write():
    # Create the SpecExecutor
    se = dse.SpecExecutor()
    se.reg = [0, 0]

    # Create a memory slot
    se.current_memory = dse.MemorySlot(2)
    se.current_memory.wr_ptr_aligned = 0

    # Set source registers
    se.src1_reg = 0
    se.src2_reg = 1

    return se


@pytest.fixture(params=[0, 1, 2, 3])
def offset(request):
    return request.param


@pytest.fixture(params=[2, 3, 4])
def repeat(request):
    return request.param


def test_write_byte_to_mem_array(specexec_write, offset):
    se = specexec_write
    se.current_memory.wr_ptr_offset = offset

    # Set the registers (value and n_repeats)
    se.use_src1_reg = True
    se.reg[se.src1_reg] = 0xBE
    se.use_src2_reg = True
    se.reg[se.src2_reg] = 1
    se.cmd = (0x0 << 12)  # Write a byte

    # Write
    se._write()

    # Check
    assert(se.current_memory.memory[0] == se.reg[se.src1_reg] << (offset * 8))


def test_write_half_word_to_mem_array(specexec_write, offset):
    se = specexec_write
    se.current_memory.wr_ptr_offset = offset

    # Set the registers (value and n_repeats)
    se.use_src1_reg = True
    se.reg[se.src1_reg] = 0xBEEF
    se.use_src2_reg = True
    se.reg[se.src2_reg] = 1
    se.cmd = (0x1 << 12)  # Write 2 bytes

    # Write
    se._write()

    # Check
    offset *= 8
    svalue_lower = (se.reg[se.src1_reg] << offset) & 0xFFFFFFFF
    svalue_upper = ((se.reg[se.src1_reg] << offset) >> 32) & 0xFFFFFFFF
    assert(se.current_memory.memory[0] == svalue_lower)
    assert(se.current_memory.memory[1] == svalue_upper)


def test_write_word_to_mem_array(specexec_write, offset):
    se = specexec_write
    se.current_memory.wr_ptr_offset = offset

    # Set the registers (value and n_repeats)
    se.use_src1_reg = True
    se.reg[se.src1_reg] = 0xABCDBEEF
    se.use_src2_reg = True
    se.reg[se.src2_reg] = 1
    se.cmd = (0x2 << 12)  # Write 4 bytes

    # Write
    se._write()

    # Check
    offset *= 8
    svalue_lower = (se.reg[se.src1_reg] << offset) & 0xFFFFFFFF
    svalue_upper = ((se.reg[se.src1_reg] << offset) >> 32) & 0xFFFFFFFF
    assert(se.current_memory.memory[0] == svalue_lower)
    assert(se.current_memory.memory[1] == svalue_upper)


def test_write_repeat(specexec_write, offset, repeat):
    se = specexec_write
    se.current_memory.wr_ptr_offset = offset

    # Set the registers (value and n_repeats)
    se.use_src1_reg = True
    se.reg[se.src1_reg] = 0xBE
    se.use_src2_reg = True
    se.reg[se.src2_reg] = repeat
    se.cmd = 0x0  # Write 1 bytes

    # Write
    se._write()

    # Check
    expected_lower = reduce(
        operator.or_, [0xBE << n*8 for n in range(offset, repeat+offset)]
    ) & 0xFFFFFFFF
    expected_upper = (reduce(
        operator.or_, [0xBE << n*8 for n in range(offset, repeat+offset)]
    ) >> 32) & 0xFFFFFFFF

    assert(se.current_memory.memory[0] == expected_lower)
    assert(se.current_memory.memory[1] == expected_upper)
