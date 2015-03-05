"""
Constants used by the Data Structure Generator (DSG)
and the Spec Executor
"""

# MAGIC Numbers:
DSG_MAGIC_NUM     = 0x5B7CA17E # Data spec magic number
APPDATA_MAGIC_NUM = 0xAD130AD6 # Application datafile magic number

# DSG Arrays and tables sizes:
MAX_REGISTERS       = 16
MAX_MEM_REGIONS     = 16
MAX_STRUCT_SLOTS    = 16
MAX_STRUCT_ELEMENTS = 16
MAX_PACKSPEC_SLOTS  = 16
MAX_CONSTRUCTORS    = 16
MAX_PARAM_LISTS     = 16
MAX_RNGS            = 16
MAX_RANDOM_DISTS    = 16
APP_PTR_TABLE_WORDS_SZ = 20
APP_PTR_TABLE_BYTES_SZ = APP_PTR_TABLE_WORDS_SZ * 4

# Constants used by DSG command encoding:
LEN1, LEN2, LEN3, LEN4 = 0, 1, 2, 3
NO_REGS, DEST_ONLY, SRC1_ONLY, DEST_AND_SRC1, ALL_REGS = 0, 4, 2, 6, 7

# DSG Opcode encodings:
DSG_BREAK             = 0x00
DSG_NOP               = 0x01
DSG_RESERVE           = 0x02
DSG_FREE              = 0x03
DSG_DECLARE_RNG       = 0x05
DSG_DECLARE_RANDOM_DIST = 0x06
DSG_GET_RANDOM_NUMBER = 0x07
DSG_START_STRUCT      = 0x10
DSG_STRUCT_ELEM       = 0x11
DSG_END_STRUCT        = 0x12
DSG_START_CONSTRUCTOR = 0x20
DSG_END_CONSTRUCTOR   = 0x25
DSG_CONSTRUCT         = 0x40
DSG_WRITE             = 0x41
DSG_WRITE_ARRAY       = 0x42
DSG_WRITE_STRUCT      = 0x43
DSG_BLOCK_COPY        = 0x44
DSG_SWITCH_FOCUS      = 0x50
DSG_LOOP              = 0x51
DSG_BREAK_LOOP        = 0x52
DSG_END_LOOP          = 0x53
DSG_IF                = 0x55
DSG_ELSE              = 0x56
DSG_END_IF            = 0x57
DSG_MV                = 0x60
DSG_GET_WR_PTR        = 0x63
DSG_SET_WR_PTR        = 0x64
DSG_ALIGN_WR_PTR      = 0x65
DSG_ARITH_OP          = 0x67
DSG_LOGIC_OP          = 0x68
DSG_REFORMAT          = 0x6A
DSG_COPY_STRUCT       = 0x70
DSG_COPY_PARAM        = 0x71
DSG_WRITE_PARAM       = 0x72
DSG_WRITE_PARAM_COMPONENT= 0x73
DSG_PRINT_VAL         = 0x80
DSG_PRINT_TXT         = 0X81
DSG_PRINT_STRUCT      = 0X82
DSG_END_SPEC          = 0XFF

#SDRAM
SDRAM_SIZE = 128 * 1024 * 1024
SDRAM_AVILABLE = 119 * 1024 * 1024

#Model Names
APP_MONITOR_CORE_APPLICATION_ID = 0xCAFE
IF_CURR_EXP_CORE_APPLICATION_ID = 0xCAFD
SPIKESOURCEARRAY_CORE_APPLICATION_ID = 0xCAFC
SPIKESOURCEPOISSON_CORE_APPLICATION_ID = 0xCAFB
SPIKESOURCEREMOTE_CORE_APPLICATION_ID = 0xCAFA
DELAY_EXTENSION_CORE_APPLICATION_ID = 0xCADE
EXTERNAL_MOTER_DEVICE_CORE_APPLICATION_ID = 0xCADD
EXTERNAL_COCHLEA_DEVICE_CORE_APPLICATION_ID = 0xCADC
EXTERNAL_RETINA_DEVICE_CORE_APPLICATION_ID = 0xCADB
EXTERNAL_RETINA_SETUP_DEVICE_CORE_APPLICATION_ID = 0xCADA
EXTERNAL_FPGA_RETINA_DEVICE_CORE_APPLICATION_ID = 0xCACF
EXTERNAL_SPIKE_SOURCEE_CORE_APPLICATION_ID = 0xCACE

#memory Locations
CORE_MAP_ADDRESS = 0x77700000
ROUTING_TABLE_ADDRESS = 0x77780000

#memory ids
SDRAM_BASE_ADDR = 0x70000000
APP_START_ADDR = 0x404000

DSG_LIB_VER_MAJ = 0x0000     # Version 0.1 of the DSG library used
DSG_LIB_VER_MIN = 0x0001
# Indices for entries in mem array list:
REGION_ID      = 0 # The slot number for this region
WR_PTR_ALIGNED = 1 # the current word aligned write pointer within this region
WR_PTR_OFFSET  = 2 # offset of the write pointer within the word
REGION_SZ  = 3    # The size (in words) of this region
MEM_ARRAY  = 4    # Region content - a numpy array of words
LEAVE_UNFILLED = 5 # If '1', memory region not written to file.

# Random number generator state indices:
RNG_SOURCE = 0
RND_SEED   = 1
RNG_STATE  = 2
RNG_VALUES = 3
# Indices for entries in loop list:
LOOP_REG      = 0
LOOP_STARTVAL = 1
LOOP_ENDVAL   = 2
LOOP_INC      = 3
LOOP_RESTART_ADDR = 4
# Indices for entries in command params list:
CMDLEN       = 0
OPCODE       = 1
USE_DEST_REG = 2
DEST_REG     = 3
USE_SRC1_REG = 4
SRC1_REG     = 5
SRC1_VAL     = 6
USE_SRC2_REG = 7
SRC2_REG     = 8
SRC2_VAL     = 9
# Indices for elements in parameter structures:
ELEM_VAL  = 0
ELEM_TYPE = 1
ELEM_LEN  = 2

# used to check that each of our default models
     # are being called with the default mask
DEFAULT_APP_MASK = 0xfffffc00
