"""
Module:  data_spec_gen.py
Created: 24/7/13
Version: 0.1
Author:  Simon D.

Description:
   Contains a library of functions used by any Data Specification Generator
   function to construct the Data Spec required for its application. Each app
   requires at least one Data Spec. Some, such as neural networks, require a
   different data stucture for each neuron type and more than one Spec Generator
   function is required.

   A DataSpec is a variable attached to a Processor during initialisation of the
   machine object. The DataSpecGenerator function is a method defined as part of
   the model class for each model type. It calls functions defined here to build
   up a list of SpecInstructions. These instructions are replayed by the
   SpecExecutor (either on the host, or on the target core itself) to construct
   the data structures.
"""


import math
import os
import numpy
from pacman103.core import exceptions
from pacman103.lib import data_spec_constants

import logging
import ctypes
logger = logging.getLogger(__name__)

DSG_LIB_VER_MAJ = 0x0000     # Version 0.1 of this library
DSG_LIB_VER_MIN = 0x0001
DsgVersionMaj = 0
DsgVersionMin = 1

# Array indices for Struct Arrays:
ELEM_IDX = 0
ELEM_DATA_TYPE = 1
ELEM_LABEL = 2
ELEM_VALUE = 3

class DataSpec:
    """
    An instance of this class represents a single core-specific specification
    of the data files necessary to run the allocated task on that core.
    """

    def __init__(self, processor=None, dao=None):
        self.processor        = processor
        self.instructions     = list()
        self.file_name         = None
        self.file_handle_bin    = None
        self.write_binary_specs = dao.writeBinarySpecs
        self.file_handle_txt    = None
        self.write_text_specs   = dao.writeTextSpecs
        self.instruction_counter = 8  # Account for 8 word header
        self.in_constructor    = False
        self.in_pack_spec       = False
        self.current_mem_slot   = 0
        self.current_mem_ptr    = 0
        self.mem_slot          = list()
        self.struct_list       = list()
        self.packed_spec_list   = list()
        self.params_list       = list()
        self.constructor_list  = list()
        self.rng_list          = list()
        self.rand_dist_list     = list()
        self.dao              = dao
        self.cmdIdx           = 1
        self.txt_indent        = 0
        self.data_spec_exec = dao.spec_executor
        for i in range(data_spec_constants.MAX_MEM_REGIONS): self.mem_slot.append(0)
        for i in range(data_spec_constants.MAX_STRUCT_SLOTS): self.struct_list.append(False)
        for i in range(data_spec_constants.MAX_RNGS): self.rng_list.append(False)
        for i in range(data_spec_constants.MAX_RANDOM_DISTS): self.rand_dist_list.append(False)
        
        # Data-type encoding
        # Spec writers can use textual description for data types
        # but these are translated into a 5-bit value for encoding:
        self.dataTypes = { 
           "uint8": 0x00, "uint16": 0x01, "uint32": 0x02, "uint64": 0x03,\
            "int8": 0x04,  "int16": 0x05,  "int32": 0x06,  "int64": 0x07,\
             "u88": 0x08,  "u1616": 0x09,  "u3232": 0x0A,  "s2111": 0x0B, "s511": 0x0C,\
             "s87": 0x0D,  "s1615": 0x0E,  "s3231": 0x0F,\
             "u08": 0x10,   "u016": 0x11,   "u032": 0x12,   "u064": 0x13,\
             "s07": 0x14,   "s015": 0x15,   "s031": 0x16,   "s063": 0x17,\
          "float" : 0x18
        }
        
        self.dataTypesSigned = {
          "uint8": 0, "uint16": 0, "uint32": 0, "uint64": 0, \
           "int8": 1,  "int16": 1,  "int32": 1,  "int64": 1, \
            "u88": 0,  "u1616": 0,  "u3232": 0,  "s2111": 0, "s511": 1, \
            "s87": 1,  "s1615": 1,  "s3231": 1,    
            "u08": 0,   "u016": 0,  "u032": 0,   "u064": 0,
            "s07": 1,   "s015": 1,  "s031": 1,   "s063": 1,  
            "float": 1
        }
        
        self.dataTypesLength = {
          "uint8": 1, "uint16": 2, "uint32": 4, "uint64": 8,\
           "int8": 1,  "int16": 2,  "int32": 4,  "int64": 8,\
            "u88": 2,  "u1616": 4,  "u3232": 8,  "s2111": 4, "s511": 2,\
            "s87": 2,  "s1615": 4,  "s3231": 8,\
            "u08": 1,   "u016": 2,   "u032": 4,   "u064": 8,
            "s07": 1,   "s015": 2,   "s031": 4,   "s063": 8,\
           "float": 4
        }
        
        # Encoding for conditions used by If statement:
        self.condition_dict = {
               "==": 0x00, "!=": 0x01, "<=": 0x02, "<": 0x03, \
               ">=": 0x04,  ">": 0x05, "isZero":0x06,         \
               "notZero":0x07 }
        return

    """ *** Functions to open and close the Spec File *** """

    def initialise(self, AppId, dao):
        """
        Opens the output file and writes standard header information that
        the user need not worry about.
        """
        # Open Spec file and write header:
        self.openSpecFile(self.processor)
        timerPeriod = dao.time_scale_factor * dao.machineTimeStep
        DsgVersion = DsgVersionMaj * pow(2,16) + DsgVersionMin  # Format 0000_0000
        self.writeHeaderInfo(self.processor, AppId, DsgVersion, timerPeriod)
        return

    def openSpecFile(self, processor):
        """
        Opens the output file that will contain a Data Spec.
        If the dao.writeTextSpecs flag is True, also open a text
        file to provide a user-readable version.
        """
        x, y, p = processor.get_coordinates()
        hostname = processor.chip.machine.hostname
        fNameBin = self.dao.get_binaries_directory() + os.sep \
                      + "%s_dataSpec_%d_%d_%d.dat" % (hostname, x, y, p)
        fNameTxt = self.dao.get_reports_directory("dataSpec") + os.sep \
                    + "%s_dataSpec_%d_%d_%d.txt" % (hostname, x, y, p)
        self.file_name = fNameBin
        if self.write_binary_specs and self.data_spec_exec is None:
            logger.debug("Writing spec to %s", fNameBin)
            self.file_handle_bin = open(fNameBin, "wb", 8192)
        if self.write_text_specs:
            logger.debug("Writing text spec to %s", fNameTxt)
            self.file_handle_txt = open(fNameTxt, "w", 8192)
        return


    def writeHeaderInfo(self, processor, appID, appDsgVersion, timerPeriod):
        """
        Write the boiler-plate information to the spec. This is used
        by disassembly tools to identify a DataSpec when trying to decypher
        it.
        """
        dsgLibVersion = DSG_LIB_VER_MAJ * 16 + DSG_LIB_VER_MIN
        (x, y, p) = processor.get_coordinates()
        targetProcessor = x * 256 + y * 16 + p

        # Construct header information:
        headerData = numpy.array([data_spec_constants.DSG_MAGIC_NUM,
                                  dsgLibVersion,
                                  appDsgVersion,
                                  appID,
                                  targetProcessor,
                                  timerPeriod, 0, 0],
                                  dtype="uint32")

        # Write header to file:
        if self.write_binary_specs:
            if self.data_spec_exec is not None:
                self.data_spec_exec.write_header(headerData)
            else:
                headerData.tofile(self.file_handle_bin)

        # Write text version of header to text file, if required:
        if self.write_text_specs:
            self.file_handle_txt.write("# Data Specification ")
            self.file_handle_txt.write("(MAGIC_NUMBER = 0x%X)\n" % data_spec_constants.DSG_MAGIC_NUM)
            self.file_handle_txt.write("# DSG library version: %d.%d\n" %      \
            (DSG_LIB_VER_MAJ, DSG_LIB_VER_MIN))
            appDsgVersionMaj = appDsgVersion/16
            appDsgVersionMin = appDsgVersion & 15
            self.file_handle_txt.write("# App-specific DSG version: %d.%d\n"   \
            % (appDsgVersionMaj, appDsgVersionMin))
            self.file_handle_txt.write("# Application Identifier: 0x%X\n" % appID)
            self.file_handle_txt.write("#\n# Target Machine: Not identified\n")
            self.file_handle_txt.write("#\n# Target Processor: (%d, %d, %d)\n" \
            % processor.get_coordinates())
        return

    def closeSpecFile(self):
        """
        Close the Spec File, as well as the textual version of the Spec, if
        this was also opened.
        """
        if self.write_binary_specs and self.data_spec_exec is None:
            self.file_handle_bin.close()
            self.file_handle_bin = None
        if self.write_text_specs:
            self.file_handle_txt.close()
            self.file_handle_txt = None
        return

    """
    Functions that generate single or multiple Spec commands
    """

    def comment(self, textComment=None):
        """
        Write the given text directly to the text version of the data spec,
        to provide some additional information to readers.
        """
        cmdWordList = [] # Nothing appears in the binary file
        cmdString = textComment
        self.writeCommandToFiles(cmdWordList, cmdString, noInstructionNumber = True)
        return

    def execBreak(self):
        """
        CMD_CODE: 0x00, BREAK
        Terminate the execution of this spec and raise an exception. Used in debug.
        """
        cmdWord = (data_spec_constants.LEN1<< 28) | (data_spec_constants.DSG_BREAK<<20)
        cmdWordList = [cmdWord]
        cmdString = "BREAK"
        self.writeCommandToFiles(cmdWordList, cmdString)
        return

    def execNOP(self):
        """
        CMD_CODE: 0x01, NOP
        Execute a no-operation. Does nothing.
        """
        cmdWord = (data_spec_constants.LEN1<< 28) | (data_spec_constants.DSG_NOP<<20)
        cmdWordList = [cmdWord]
        cmdString = "NOP"
        self.writeCommandToFiles(cmdWordList, cmdString)
        return

    """
        *** Commands to reserve and free memory regions ***
    """
    def reserveMemRegion(self, region, size, label=None, leaveUnfilled = False):
        """
        CMD_CODE: 0x02, RESERVE
        Reserve space in SDRAM for a data structure to be built later.
        A second data word is used to specify the amount of data in bytes that
        is required.
        The leaveUnfilled flag is used when reserving space for results. When
        true, the region is not filled with data. It is used to reserve space
        in the memory map for results to be placed during simulation.
        TODO: Implement the internals required for the leaveUnfilled flag.
        """

        if (region<0) or (region>data_spec_constants.MAX_MEM_REGIONS):
            logger.error("Error: Memory region requested (%d) is out of range 0 to %d.\n"
                % (region, data_spec_constants.MAX_MEM_REGIONS - 1))
            raise exceptions.DsgSpecCmdException(
                'Spec. command error while generating file \'%s\'\n' 
                % self.file_name)
        if self.mem_slot[region] != 0:
            errorStr = "Error: Requested memory region (%d) " % region
            errorStr = errorStr + "is already allocated.\n"
            logger.error(errorStr)
            raise exceptions.DsgSpecCmdException(
                'Spec. command error while generating file \'%s\'\n' 
                % self.file_name)

        self.mem_slot[region] = [size, label]
        if ((self.processor.chip.sdramUsed + size) 
                > data_spec_constants.SDRAM_SIZE):
            usedK = int(self.processor.chip.sdramUsed/1024.0)
            errorStr = "Error: Reserved memory request (%d bytes) " % size
            errorStr = errorStr + "has exhausted available SDRAM for this chip"
            errorStr = errorStr + " (%dK was already allocated)." % usedK
            logger.error(errorStr)
            raise exceptions.DsgSpecMemAllocException(
                'Spec. command error while generating file \'%s\'\n' 
                % self.file_name)

        # Add new region size to running total of sdram usage:
        self.processor.chip.sdramUsed = self.processor.chip.sdramUsed + size

        unfilled = 0
        if leaveUnfilled:
            unfilled = 1
        # Length [29:28], command[27:20], field_use[18:16], unfilled[7],
        # region ID [4:0]:
        cmdWord = (data_spec_constants.LEN2<< 28) | \
                  (data_spec_constants.DSG_RESERVE<<20) | \
                  (data_spec_constants.NO_REGS<<16) | \
                                    (unfilled<<7) | (region)
        cmdWordList = [cmdWord, size]
        if leaveUnfilled == True:
            unfilledString = "UNFILLED"
        else:
            unfilledString = ""
        if label is None:
            cmdString = "RESERVE memRegion=%d sz=%d %s" % (region, size, unfilledString)
        else:
            cmdString = "RESERVE memRegion=%d sz=%d label='%s' %s" % \
                         (region, size, label, unfilledString)
        # Send the command to the output files:
        self.writeCommandToFiles(cmdWordList, cmdString)


    def freeMemoryBlock(self, region):
      """
      CMD_CODE: 0x3, FREE
      Release memory reserved earlier. (May not be required)
      """
      pass



    """
       *** Functions related to Random Numbers and Associated Distributions ***
    """

    def declareRNG(self, rngId=0, source='default', seed=1):
        """
        CMD_CODE: 0x05, DECLARE_RNG
        Declare a Random Number Generator (RNG) to be used either directly
        to extract uniformly distributed numbers between 0.0 and 1.0, or
        more usually, to feed a wrapper RandomDistribution object that will
        convert it into a number drawn from a different distribution.
        Multiple RNG sources are supported, indexed using rngId.
        """
        if rngId <0 or rngId > 15:
            self.checkRegisterRange(rngId, "DECLARE_RNG: Slot ID")
        # Source field is constant for now, may allow multiple different
        # sources of random numbers later.
        rngSource   = 0x0
        cmdWord     = (data_spec_constants.LEN2<<28) | \
                      (data_spec_constants.DSG_DECLARE_RNG<<20)
        cmdWord     = cmdWord | (rngId<<12) | (rngSource<<8)
        cmdWordList = [cmdWord, seed]
        cmdString   = "DECLARE_RNG id=%d, source=%d, seed=%d" \
               % (rngId, rngSource, seed)
        self.writeCommandToFiles(cmdWordList, cmdString)

    def declareRandomDistribution(self, distId=0, paramList=0):
        """
        CMD_CODE: 0x06, DECLARE_RANDOM_DIST
        Declares a new random distribution, passing a pre-defined parameter list
        with the following structure:
        {
           uint32 distType; // 0 = uniform, 1 = normal, others=RESERVED
           s1615  rangeMin; // Minimum value of random number
           s1615  rangeMax; // Maximum value of random number
           uint32 rngId     // Slot ID of the source Random Number Generator
        }
        To draw a number from this distribution, use GET_RANDOM_NUMBER (0x07)
        """
        if distId<0 or distId > 63:
            errorString = "DECLARE_RANDOM_DIST: Distribution ID not in range 0->63"
            raise exceptions.DsgSpecCmdException(errorString)
        cmdWord  = (data_spec_constants.LEN1<<28) | \
                   (data_spec_constants.DSG_DECLARE_RANDOM_DIST<<20)
        cmdWord  = cmdWord |(distId<<8) |(paramList)
        cmdString= "DECLARE_RANDOM_DIST distId=%d, paramList=%d" \
               % (distId, paramList)
        self.writeCommandToFiles([cmdWord], cmdString)

    def getRandomNumber(self, distId=0, destReg=0):
        """
        CMD_CODE: 0x07, GET_RANDOM_NUMBER
        Returns a random number drawn from the specified distribution, writing it
        to the given register.
        The random number returned is represented in s1615 format.
        """
        if distId<0 or distId>63:
            errorString = "GET_RANDOM_NUMBER: Distribution ID not in range 0->63"
            raise exceptions.DsgSpecCmdException(errorString)
        if destReg<0 or destReg>15:
            errorString = "GET_RANDOM_NUMBER: Destintion register ID not in range 0->15"
            raise exceptions.DsgSpecCmdException(errorString)
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_GET_RANDOM_NUMBER<<20)
        cmdWord = cmdWord    |(destReg<<12) | (distId)
        cmdString= "GET_RANDOM_NUMBER distId=%d, destReg=%d" % (distId, data_spec_constants.reg)
        self.writeCommandToFiles([cmdWord], cmdString)


    """
        *** Commands to declare objects: structs, specs and constructors ***
    """

    def defineStruct(self, structId, definition, name=None):
        """
        Used to define a single structure with parameters.
        Generates multiple spec commands.
        """
        structId = structId & 0x1F # only range 0->31 permitted
        if structId < 0 or structId > 31:
            errorString = "Define STRUCT: Struct ID (%d) out of range 0->31."\
                           % structId
            self.raiseDsgSpecCmdException(errorString)

        # Write START_STRUCT command to array:
        cmdWord = (data_spec_constants.LEN1<<28) |\
                  data_spec_constants.DSG_START_STRUCT<<20 | structId
        cmdString = "START_STRUCT id=%d, label=%s {" \
               % (structId, name)
        self.writeCommandToFiles([cmdWord], cmdString, indent = True)

        # Write series of STRUCT_ELEM instructions, one per field in
        # the struct definition:
        for element in definition:
            elemIdx, elemType, elemLabel = element[ELEM_IDX],       \
                                           element[ELEM_DATA_TYPE], \
                                           element[ELEM_LABEL]
            if len(element) > 3:
                elementValue = element[ELEM_VALUE]
            else:
                elementValue = 0

            # Limit element index to 5-bits:
            elemIdx = elemIdx&0x1F
            # Translate the textual data type to internal encoding:
            if elemType in self.dataTypes:
                typeEncoding = self.dataTypes[elemType]
            else:
                errorString = "STRUCT_ELEM: Data type \'%s\' not recognised." \
                               % elemType
                self.raiseDsgSpecCmdException(errorString)
            cmdWord = (data_spec_constants.LEN2<<28) | \
                      (data_spec_constants.DSG_STRUCT_ELEM<<20) | (elemIdx<<8) \
                                                         | (typeEncoding)
            cmdString = "STRUCT_ELEM index=%d, type=%s, label=\'%s\'"\
                % (elemIdx, elemType, elemLabel)
            self.writeCommandToFiles([cmdWord, elementValue], cmdString)

        # Finish off by sending an END_STRUCT command to close the definition:
        cmdWord = (data_spec_constants.LEN1<28) | \
                  (data_spec_constants.DSG_END_STRUCT<<20)
        cmdString = "} END_STRUCT"
        self.writeCommandToFiles([cmdWord], cmdString, outdent = True)
        self.struct_list[structId] = True

    def createParamList(self, paramListId, srcStructId, definition, name = None):
        """
        Creates a series of Spec commands to instantiate a previously
        declared struct and assign values to its elements.
        """
        numElements = len(definition)
        # How many words needed for the entire param list definition?:
        numWords = 2  # Already need START_STRUCT and END_STRUCT
        for elem in definition:
          dataLen = elem[ELEM_DATA_TYPE]
          if dataLen > 2:
            numWords += 2
          else:
            numWords +=1

        cmdWords = numpy.zeros(numWords, dtype='uint32')

        paramsId = paramListId & 0x1F # only range 0->31 permitted
        structId = srcStructId & 0x1F # only range 0->31 permitted

        # Assign command to create the param structure:
        cmdWords[0] = data_spec_constants.DSG_START_PARAMS<<24 | \
                      paramsId <<16 | structId<<8
        if self.write_text_specs is not None:
          self.file_handle_txt.write( \
          "START_PARAMS paramsId=%s, structId=%s, label=%s" \
          % (paramsId, structId, name))

        # Write individual ASSIGN_PARAM commands to give values
        # to each listed element:
        elemCount = 0
        for element in definition:
          elemIdx, elemType, elemValue = element[0], element[1], element[2]
          # elemIdx is the index of this element in the struct:
          elemIdx = elemIdx&0x1F
          # If there's a 32-bit immediate, add it afterwards:
          if elemType == 32:
            opcode = data_spec_constants.DSG_ASSIGN_PARAM | \
                     data_spec_constants.PLUS_DATAWORD
            cmdWords[elemCount + 1] = opcode<<24 | (0xC0|elemIdx)<<16
            # 32-bit immediate is placed in following 32-bit word:
            elemCount = elemCount + 1
            cmdWords[elemCount + 1] = elemValue
            trueValue = elemValue

          elif elemType == 16:
            # It's a 16-bit immediate, so add it in the command word:
            trueValue = elemValue & 0xFFFF
            cmdWords[elemCount + 1] = data_spec_constants.DSG_ASSIGN_PARAM<<24 | \
                                      (0x8|elemIdx)<<16 | (trueValue)
          elif elemType == 8:
            trueValue = elemValue & 0xFF
            # It's an 8-bit immediate, so add it in the command word:
            cmdWords[elemCount + 1] = data_spec_constants.DSG_ASSIGN_PARAM<<24 |\
                                      (0x4|elemIdx) | (trueValue)
          elif elemType == 0:
            # It's a register reference (r0->r15):
            trueValue = elemValue & 0x0F
            cmdWords[elemCount + 1] = data_spec_constants.DSG_ASSIGN_PARAM<<24 | \
                                      (0x0|elemIdx)<<16 | (trueValue)
          if self.write_text_specs:
            self.file_handle_txt.write("  ASSIGN_PARAM element=%d, " % elemIdx),
            if elemType == 0:
              self.file_handle_txt.write("register=%d\n" % trueValue)
            else:
              self.file_handle_txt.write("value=%d\n" % trueValue)

          # Advance pointer to next word:
          elemCount = elemCount + 1

        # Write command to close the params list:
        idxOfEndCmd = numWords - 1  # 1 + len(definition) + doubleCount
        cmdWords[idxOfEndCmd] = data_spec_constants.DSG_END_PARAMS<<24
        if self.write_text_specs is not None:
          self.file_handle_txt.write("END_PARAMS\n")

        # Write command string to the Spec file:
        cmdWords.tofile(self.file_handle_bin)

    def defineConstructor(self, constructorId=None, numArgs=0, readOnlyMask=0):
        """
        CMD_CODE: 0x20, START_CONSTRUCTOR
        Start a block of instructions that define how a block of memory
        is to be written
        """
        if constructorId is None:
            errorString = "START_CONSTRUCTOR - No constructor ID specified."
            self.raiseDsgSpecCmdException(errorString)
        if constructorId < 0 or constructorId > 31:
            errorString = "START_CONSTRUCTOR - Constructor ID (%d)" + \
                          "not in range 0->31." % constructorId
            self.raiseDsgSpecCmdException(errorString)
        if numArgs <0 or numArgs > 5:
            errorString = "START_CONSTRUCTOR - Number of arguments (%d)" + \
                          "not in range 0->5." % numArgs
            self.raiseDsgSpecCmdException(errorString)
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_START_CONSTRUCTOR<<20) | \
                  (constructorId<<11)
        cmdWord = cmdWord    | (numArgs<<8)     | (readOnlyMask & 0x1F)
        cmdString = "START_CONSTRUCTOR constructorId = %d" % constructorId
        cmdString = "%s, numArgs = %d, readOnlyMask = 0x%X"%(cmdString, numArgs, readOnlyMask)
        self.writeCommandToFiles([cmdWord], cmdString, indent = True)


    def endConstructor(self):
        """
        CMD_CODE: 0x25, END_CONSTRUCTOR
        Ends a block of instructions that define how a block of memory
        is to be written.
        """
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_END_CONSTRUCTOR<<20)
        cmdString = "END_CONSTRUCTOR"
        self.writeCommandToFiles([cmdWord], cmdString, outdent = True)


    """
         *** Commands to write blocks of data ***
    """
    def construct(self, constructorId = None, args = []):
        """
        CMD_CODE: 0x40, CONSTRUCT
        Execute a previously defined constructor program, to write a block of
        data to the currently open memory region at its current write pointer
        addess.
        """
        if constructorId is None:
            errorString = "CONSTRUCT - No constructor ID specified."
            self.raiseDsgSpecCmdException(errorString)
        elif constructorId < 0 or constructorId > 31:
            errorString = "CONSTRUCT - constructor ID (%d)" + \
                          " not in range 0->31." % constructorId
            self.raiseDsgSpecCmdException(errorString)
        if len(args)>5:
            errorString = "CONSTRUCT - Too many arguments specified."
            self.raiseDsgSpecCmdException(errorString)
        cmdString = "CONSTRUCT id = %d" % constructorId
        cmdLen = data_spec_constants.LEN1
        if args is not None:
            structIdList = 0x0
            cmdLen = data_spec_constants.LEN2
            argsList = ", args = ["
            count  = 0
            for arg in args:
                if arg < 0 or arg > 15:
                    errorString = "CONSTRUCT - argument ID (%d)" + \
                                  " not in range 0->15." % arg
                    self.raiseDsgSpecCmdException(errorString)
                if self.struct_list[arg]:
                    # Shift current list value and append new entry
                    # in bit positions [4:0]:
                    structIdList = structIdList | (arg << (5*count))
                    argsList = "%s %d" % (argsList, arg)
                    count += 1
                else:
                    errorString = "CONSTRUCT - struct ID (%d)" + \
                                  " not a valid structure." % arg
                    self.raiseDsgSpecCmdException(errorString)
            argsList = "%s]" % argsList
        cmdWord = (cmdLen<<28) | (data_spec_constants.DSG_CONSTRUCT<<20) | \
                  (constructorId<<8)
        cmdWordList = [cmdWord]
        if args is not None:
            cmdWordList.insert(1, structIdList)
            cmdString = "%s %s" % (cmdString, argsList)
        self.writeCommandToFiles(cmdWordList, cmdString)

    def write(self, dataReg=None, repeatReg=None, data=None, repeats = 1, \
                                                             sizeof='uint32'):
        """
        CMD_CODE: 0x41, WRITE
        Perform an write of one or more values. Data is held either in a
        register or added as an immediate. The number of repeats of
        the write is either an immediate embedded in the command word,
        or is in a register.
        Where a register is given for src1 (data) or src2 (num repeats) this
        value is used. Where no register is given for data, a 32-bit immediate
        is expected. Where no register is given for num_repeats, a 8-bit
        can be provided and is embedded in the 32-bit command. A default of
        a single repeat is assume if no value is given.
        """
        # How big is a data element to be written?
        elementSz = self.dataTypeLength(sizeof)
        if elementSz == 1:
            dataLen = 0
        elif elementSz == 2:
            dataLen = 1
        elif elementSz == 4:
            dataLen = 2
        elif elementSz == 8:
            dataLen = 3
        else:
            errorString = "WRITE command unsupported data type given."
            self.raiseDsgSpecCmdException(errorString)

        if repeats < 1:
          self.raiseDsgSpecCmdException("Negative repeats")

        cmdLen, parameters, regUsage = [0, 0, 0]
        cmdWordList = []
        cmdString = "WRITE"
        if dataReg is not None:
            self.checkRegisterRange(dataReg, "WRITE: data register")
            regUsage   = regUsage | 2; parameters = parameters | (dataReg<<8)
            cmdString = "%s data=reg[%d]" % (cmdString, dataReg)
        else:
            cmdLen += 1; cmdWordList.append(data)
            cmdString = "%s data = 0x%X" % (cmdString, data)
        if repeatReg is not None:
            regUsage   = regUsage | 1; parameters = parameters | (repeatReg<<4)
            cmdString = "%s, repeats = reg[%d]" % (cmdString, repeatReg)
            self.checkRegisterRange(repeatReg, "WRITE: repeat register")
        else:
            parameters = parameters | repeats & 0xFF
            cmdString = "%s, repeats = %u" % (cmdString, repeats)

        cmdWord = (cmdLen<< 28) | (data_spec_constants.DSG_WRITE<<20) | \
                  (regUsage<<16)
        cmdWord = cmdWord       | (dataLen<<12)   | (parameters)
        cmdWordList.insert(0, cmdWord)
        cmdString = "%s, dataType = %s" % (cmdString, sizeof)
        self.writeCommandToFiles(cmdWordList, cmdString)

    def write_array(self, data=None, repeats=1):
        """CMD_CODE: 0x42, WRITE_ARRAY
        Write an array of words.  The array to copy is appended after the
        instruction.
        """
        data = numpy.array(data, dtype='uint32')
        size = data.size
        fdata = numpy.reshape(data, size)

        cmd_len = 0xF
        cmd = (cmd_len << 28) | (data_spec_constants.DSG_WRITE_ARRAY << 20)

        cmd_word_list = numpy.zeros(size + 2)
        cmd_word_list[0] = cmd
        cmd_word_list[1] = size + 1
        cmd_word_list[2:] = fdata
        cmd_string = "WRITE_ARRAY, %d elements = {" % (size)
        self.writeCommandToFiles(cmd_word_list, cmd_string)

    def writeStruct(self, structId = 0, copiesReg = None, copies = 1):
        """
        CMD_CODE: 0x43, WRITE_STRUCT
        Write the contents of the given structure to the current memory
        memory at its current write pointer. By default, a single copy
        is written, but this can increased using either an immediate
        if the number is in the range 0->15 or any 32-bit value if a
        register is provided.
        """
        # Check any register value given:
        if copiesReg is not None:
            self.checkRegisterRange(copiesReg, "WRITE_STRUCT: copies register")
            regUsage    = 0x2
            copiesField = copiesReg
            paramString = ", copiesReg = %d" % copiesReg
        else:
            regUsage = 0x0
            if copies < 0 or copies > 15:
                errorString = "WRITE_STRUCT: Number of copies (%d)" % copies
                errorString = "%s not in range 0->15" % errorString
                self.raiseDsgSpecCmdException(errorString)
            else:
                copiesField = copies
                paramString = ", copies = %d" % copies
        # Check required structure ID (using register range check):
        self.checkRegisterRange(structId, "WRITE_STRUCT: structure ID")
        # Construct command:
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_WRITE_STRUCT<<20) | (regUsage<<16) | \
                  (copiesField<<8) | (structId)
        cmdString = "WRITE_STRUCT structId = %d%s" % (structId, paramString)
        self.writeCommandToFiles([cmdWord], cmdString)


    def switchWriteFocus(self, region = 0, src1Reg = None):
        """
        CMD_CODE: 0x50, SWITCH_FOCUS
        Causes the focus of memory writes to switch to a new memory region.
        This region must have been previously allocated using RESERVE.
        The write pointer for this new memory region is retained from the
        last time this memory region was the focus of attention. Initially,
        it is set to zero. The write pointer is always measured relative to
        the start of the memory region.
        """
        if src1Reg is not None:
            regUsage  = 0x2
            parameters = src1Reg & 0xF
            cmdString = "SWITCH_FOCUS memRegion = reg[%d]" % src1Reg
        else:
            regUsage   = 0x0
            parameters = region & 0xF
            cmdString  = "SWITCH_FOCUS memRegion = %d" % region

        # Is the requested region in the valid range?
        if region < 0 or region >= data_spec_constants.MAX_MEM_REGIONS:
            errorString = "Region requested for SWITCH_FOCUS command is out of range."
            self.raiseDsgSpecCmdException(errorString)
        # Has the requested region been reserved? If not, flag an error
        if self.mem_slot[region] == 0:
            errorString = "Region requested (%d) for SWITCH_FOCUS command has not been previously reserved." %region
            self.raiseDsgSpecCmdException(errorString)
        # Write command to switch focus:
        cmdWord = (data_spec_constants.LEN1<< 28) | \
                  (data_spec_constants.DSG_SWITCH_FOCUS<<20) | (regUsage<<16)
        cmdWord = cmdWord     | (parameters<<8)
        self.writeCommandToFiles([cmdWord], cmdString)


    """
        *** Commands to control execution: loops and conditionals ***
    """

    def loop(self, countReg=None, startReg=None, endReg=None, incReg=None, \
                        startVal=0, endVal=0, incVal=1):
        """
        CMD_CODE: 0x51, LOOP
        Starts a loop of instructions, using countReg as the index register.
        The start, end and increment values can be either registers or immediates.
        (If registers are used, the values are read when the LOOP initialises and
        so any subsequent changes to the registers will have no effect).
        The condition evaluates at the end of the loop after the increment.
        If regVal[countReg] < regVal[endReg] the loop is re-executed.
        """
        cmdLen      = data_spec_constants.LEN1
        paramValues = []
        regUsage    = 0x0
        # Check that registers are valid:
        if countReg is not None:
            self.checkRegisterRange(countReg, "LOOP: count register")
            paramString = "countReg = %d" % countReg
        else:
            errorString = "LOOP: No count register specified. Illegal syntax."
            self.raiseDsgSpecCmdException(errorString)

        if startReg is not None:
            self.checkRegisterRange(startReg, "LOOP: start register")
            paramString = "%s, startReg = %d" % (paramString, startReg)
            regUsage = regUsage | 0x4
            sReg     = startReg
        else:
            paramString = "%s, startVal = %d" % (paramString, startVal)
            cmdLen = cmdLen + 1
            paramValues.append(startVal)
            sReg     = 0x0

        if endReg is not None:
            self.checkRegisterRange(endReg, "LOOP: end register")
            paramString = "%s, endReg = %d" % (paramString, endReg)
            regUsage = regUsage | 0x2
            eReg     = endReg
        else:
            paramString = "%s, endVal = %d" % (paramString, endVal)
            cmdLen = cmdLen + 1
            paramValues.append(endVal)
            eReg     = 0x0

        if incReg is not None:
            self.checkRegisterRange(incReg, "LOOP: inc register")
            paramString = "%s, incReg = %d" % (paramString, incReg)
            regUsage = regUsage | 0x1
            iReg     = incReg
        else:
            paramString = "%s, incVal = %d" % (paramString, incVal)
            cmdLen = cmdLen + 1
            paramValues.append(incVal)
            iReg     = 0x0

        # Assemble command and write to file:
        cmdWord = (cmdLen<<28) | data_spec_constants.DSG_LOOP<<20 | (regUsage<<16)
        cmdWord = cmdWord | (sReg<<12) | (eReg<<8) | (iReg<<4) | (countReg)

        # Create list of command words from basic command word plus
        # the list of optional parameters:
        cmdWordList = paramValues
        cmdWordList.insert(0, cmdWord)
        words = numpy.array(cmdWordList, dtype="uint32")
        cmdString = "LOOP %s {" % (paramString)
        self.writeCommandToFiles(words, cmdString, indent = True)


    def breakLoop(self):
        """
        CMD_CODE: 0x52, BREAK_LOOP
        Causes the current loop to be exited immediately.
        """
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_BREAK_LOOP<<20)
        words = numpy.array(cmdWord, dtype="uint32")
        cmdString = "BREAK_LOOP"
        self.writeCommandToFiles([cmdWord], cmdString)

    def endLoop(self):
        """
        CMD_CODE: 0x53, END_LOOP
        Signals the end of a loop.
        """
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_END_LOOP<<20)
        words = numpy.array(cmdWord, dtype="uint32")
        cmdString = "} END_LOOP"
        self.writeCommandToFiles([cmdWord], cmdString, outdent = True)


    def ifTrue(self, src1Reg=None, condition=None, src2Reg=None, data=0):
        """
        CMD_CODE: 0x55, IF
        Performs a condition check. If the condition passes, the
        following instructions are executed. if it fails, control
        skips ahead to the instruction following the associated ELSE or
        END_IF instruction.
        Only signed 32-bit checks supported at present.
        Conditions: 0x0: EQUAL, 0x1: NOT_EQUAL, 0x2: LESS_OR_EQUAL
                    0x3: LESS_THAN,  0x4: GREATER_OR_EQUAL,
                    0x5: GREATER_THAN, 0x6: IS_ZERO (source 1 check only)
                    0x7: IS_NOT_ZERO (source 1 check only)
        """
        if src1Reg is not None:
            self.checkRegisterRange(src1Reg, "IF: source 1 register")
            regUsage = 0x2   # Source 1 is a register
            src1RegNum = src1Reg
            paramString = "reg[%d]"% src1Reg
        else:
            errorString = "IF - source 1 register not specified."
            self.raiseDsgSpecCmdException(errorString)
        # Convert condition to encoded value:
        if condition in self.condition_dict:
            encodedCondition = self.condition_dict[condition]
            paramString = "%s %s" % (paramString, condition)
        else:
            raise exceptions.DSGSpecCmdException(\
            "ERROR: DSG IF condition - Unrecognized condition used. Exiting.")
        if src2Reg is not None:
            self.checkRegisterRange(src2Reg, "IF: source 2 register")
            regUsage = 0x3   # Sources 1 and 2 are registers
            src2RegNum = src2Reg
            cmdLen = data_spec_constants.LEN1
            if (condition != 'isZero') and (condition != 'notZero'):
                paramString = "%s reg[%d]" % (paramString, src2Reg)
        else:
            cmdLen = data_spec_constants.LEN2    # Source 2 is immediate data
            src2RegNum = 0
            if (condition != 'isZero') and (condition != 'notZero'):
                paramString = "%s %d" % (paramString, data)
        # Encode instruction and write to files:
        cmdWord = (cmdLen<<28) | (data_spec_constants.DSG_IF<<20) | (regUsage<<16) | \
                  (src1RegNum<<8) | (src2RegNum<<4) | encodedCondition
        cmdString = "IF %s THEN" % paramString
        if cmdLen == data_spec_constants.LEN1:
            self.writeCommandToFiles([cmdWord], cmdString, indent = True)
        else:
            self.writeCommandToFiles([cmdWord, data], cmdString, indent = True)

    def elseClause(self):
        """
        CMD_CODE: 0x56, ELSE
        Executes the else part of an associated If instruction.
        Instructions between this and the closing END_IF are only
        executed if the original condition failed.
        """
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_ELSE<<20)
        words = numpy.array(cmdWord, dtype="uint32")
        cmdString = "ELSE"
        self.writeCommandToFiles([cmdWord], cmdString, outdent = True, indent = True)
        return

    def endIf(self):
        """
        CMD_CODE: 0x57, END_IF
        Closes the IF instruction executed earlier.
        """
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_END_IF<<20)
        words = numpy.array(cmdWord, dtype="uint32")
        cmdString = "END_IF"
        self.writeCommandToFiles([cmdWord], cmdString, outdent = True)
        return


    """
         ***  Commands to assign data to registers, etc ***
    """

    def moveToReg(self, destReg, src1Reg = None, data = None):
        """
        CMD_CODE: 0x60, MV
        Assign an immediate value or another register value to a register
        """
        # Check that we have a valid destination register:
        self.checkRegisterRange(destReg, "MV: Destination register")
        if src1Reg  is not None:
            # Build command to move between registers:
            cmdWord  = (data_spec_constants.LEN1<<28) | \
                       (data_spec_constants.DSG_MV<<20) | \
                       (data_spec_constants.DEST_AND_SRC1<<16) | \
                       (destReg<<12) | (src1Reg<<8)
            cmdWordList = [cmdWord]
            cmdString = "reg[%d] = reg[%d]" % (destReg, src1Reg)
        else:
            # Build command to assign from an immediate:
            # command has a second word (the immediate)
            cmdWord  = (data_spec_constants.LEN2<<28) | \
                       (data_spec_constants.DSG_MV<<20) | \
                       (data_spec_constants.DEST_ONLY<<16) | (destReg<<12)
            cmdWordList = [cmdWord, data]
            cmdString = "reg[%d] = %d (0x%X)" % (destReg, data, data)

        self.writeCommandToFiles(cmdWordList, cmdString)


    def getWritePtr(self, destReg):
        """
        CMD_CODE: 0x63, GET_WRITE_PTR
        Take the current write pointer and write it to a register.
        As a sider-effect, the data type of the target register is
        changed to 'uint32'
        """
      # Get destination register number:
        if destReg<0 or destReg>15:
            errorString = "DSG - GET_WR_PTR, target register (%d) out of range 0->15."%destReg
            self.raiseDsgSpecCmdException(errorString)
        regUsage = 0x4
        cmdWord  = (data_spec_constants.LEN1<<28) | \
                   (data_spec_constants.DSG_GET_WR_PTR<<20)
        cmdWord  = cmdWord    | (regUsage<<16) | (destReg <<12)
        cmdString = "GET_WR_PTR destReg = %d\n"%destReg
        self.writeCommandToFiles([cmdWord], cmdString)


    def setWritePtr(self, src1Reg = None, data = 0, relativeAddr = False):
        """
        CMD_CODE: 0x64, SET_WR_PTR
        Set the current write pointer to a new location, relative to
        either the start of the block or the current write pointer.
        Data value is either passed in the first source register or is
        a following 32-bit immediate. The choice between relative
        and absolute offset is passed in an immediate 1-bit value.
        """
        # Set relative/absolute bit:
        if relativeAddr is True:
            relAddr = 1
        else:
            relAddr = 0
        if src1Reg is not None:
            # Value comes from source register, so check its ID number:
            self.checkRegisterRange(src1Reg, "SET_WR_PTR: Source register")
            regUsage = 0x2
            cmdWord = (data_spec_constants.LEN1<<28) |\
                      (data_spec_constants.DSG_SET_WR_PTR<<20) | (regUsage<<16)
            cmdWord = cmdWord    | (src1Reg<<8)         | (relAddr)
            cmdWordList = [cmdWord]
            cmdString = "SET_WR_PTR src1Reg = %d\n" % src1Reg
        else:
            # Data is an immediate, following the command word:
            regUsage = 0x0
            cmdWord = (data_spec_constants.LEN2<<28) | \
                      (data_spec_constants.DSG_SET_WR_PTR<<20) | (regUsage<<16)
            cmdWord = cmdWord    | (relAddr)
            cmdWordList = [cmdWord, data]
            cmdString = "SET_WR_PTR data = %d" % data
        self.writeCommandToFiles(cmdWordList, cmdString)


    def alignWrPtr(self, destReg = None, src1Reg = None, data = 0):
        """
        CMD_CODE: 0x65, ALIGN_WR_PTR
        Writes zeroes to pad out the data block until it is aligned with a
        boundary of size given in the register or immediate. The new write
        pointer can be returned in a register, if required.
        """
        regUsage = 0
        if destReg is not None:
            self.checkRegisterRange(destReg, "ALIGN_WR_PTR: Destination register")
            cmdString = "ALIGN_WR_PTR "
        else:
            cmdString = "ALIGN_WR_PTR destReg = %d" % destReg
            regUsage    = regUsage | 0x4   # Dest reg used
        if src1Reg is not None:
            self.checkRegisterRange(src1Reg, "ALIGN_WR_PTR: Source register")
            cmdString = "%s, src1Reg = %d " % (cmdString, src1Reg)
            immBoundary = 0
            regUsage    = regUsage | 0x2   # Src1 reg used
        else:
            # Boundary value given in immediate (0->31 supported):
            immBoundary = data & 0x1F
            src1Reg     = 0
            cmdString   = "%s, boundary = %d" % (cmdString, immBoundary)

        cmdWord = (data_spec_constants.LEN1<<28) |\
                  (data_spec_constants.DSG_ALIGN_WR_PTR<<20) | (regUsage<<16)
        cmdWord = cmdWord    | (destReg << 12) | (src1Reg<<8) | (immBoundary)
        self.writeCommandToFiles([cmdWord], cmdString)

    def ADD(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x67, with sub-opcode 0x00
        Performs a 32-bit signed addition of sources 1 and 2, storing
        the result in the given destination register.
        """
        opcode    = 0x67      # Arith-type
        subOpcode = 0x00      # ADD operation
        subOpcodeName = "ADD"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def SUB(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x67, with sub-opcode 0x01
        Performs a signed 32-bit subtraction of source 2 from source 1,
        storing the result in the given destination register.
        """
        opcode    = 0x67      # Arith-type
        subOpcode = 0x01      # SUB operation
        subOpcodeName = "SUB"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def MUL(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x67, with sub-opcode 0x02
        Performs 32-bit signed multiplication of sources 1 and 2,
        storing the result in the given destination register.
        """
        opcode    = 0x67      # Arith-type
        subOpcode = 0x02      # MUL operation
        subOpcodeName = "MUL"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def LSL(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x68, with sub-opcode 0x00
        Performs a logical-shift-left of source 1 by a distance given by source
        2, storing the result in the given destination register.
        """
        opcode    = 0x68      # Logical-type
        subOpcode = 0x00      # LSL operation
        subOpcodeName = "LSL"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def LSR(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x68, with sub-opcode 0x01
        Performs a logical-shift-left of source 1 by a distance given by source
        2, storing the result in the given destination register.
        """
        opcode    = 0x68      # Logical-type
        subOpcode = 0x01      # LSR operation
        subOpcodeName = "LSR"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def OR(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x68, with sub-opcode 0x02
        Performs a logical-OR between the two sources, storing the result
        in the given destination register.
        """
        opcode    = 0x68      # Logical-type
        subOpcode = 0x02      # OR operation
        subOpcodeName = "OR"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def AND(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x68, with sub-opcode 0x03
        Performs a logical AND between the two sources, storing the result
        in the given destination register.
        """
        opcode    = 0x68      # Logical-type
        subOpcode = 0x03      # AND operation
        subOpcodeName = "AND"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def XOR(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x68, with sub-opcode 0x04
        Performs a logical-XOR between the two sources, storing the result
        in the given destination register.
        """
        opcode    = 0x68      # Logical-type
        subOpcode = 0x04      # XOR operation
        subOpcodeName = "XOR"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def NOT(self, destReg = None, src1Reg = None, src2Reg = None, data = 0):
        """
        CMD_CODE: 0x68, with sub-opcode 0x05
        Performs a logical-inversion of source 1, storing the result in the
        given destination register.
        """
        opcode    = 0x68      # Logical-type
        subOpcode = 0x05      # NOT operation
        subOpcodeName = "NOT"
        twoSrcOperands = True
        self.arithLogicOp(opcode, subOpcode, subOpcodeName, twoSrcOperands, \
                       destReg, src1Reg, src2Reg, data)
        return

    def arithLogicOp(self, opcode = None, subOpcode = None,        \
                    subOpcodeName = "None", twoSrcOperands = True, \
                  destReg = None, src1Reg = None, src2Reg = None,  \
                     data = 0):
        """
        CMD_CODE: 0x68, Logical_OP - specific operation is a parameter
        Performs a logical operation between the two sources, storing the result
        in the given destination register. The specific operation is held in a
        sub-opcode field, passed into this function.
        """
        # Set default values:
        cmdLen, regUsage, dReg, s1Reg, s2Reg = \
            [data_spec_constants.LEN1, 0, 0, 0, 0]
        errorString = "DSG - %s," % subOpcodeName
        if (src1Reg is None) & (src2Reg is None):
            errorString = "%s no source register given. Illegal." % (errorString)
            self.raiseDsgSpecCmdException(errorString)

        if destReg is not None:
            self.checkRegisterRange(destReg, "%s: destination register"%subOpcodeName)
            regUsage = 0x4
            dReg = destReg
            paramsString = "destReg = %d" % dReg
        else:
            # No destination register - not valid encoding
            errorString = "%s no destination register specified." % errorString
            self.raiseDsgSpecCmdException(errorString)

        if src1Reg is not None:
            self.checkRegisterRange(src1Reg, "%s: source 1 register"%subOpcodeName)
            regUsage = regUsage | 0x2
            s1Reg    = src1Reg
            paramsString = "%s, src1Reg = %d" %(paramsString, s1Reg)
        else:
            # Use immediate data, added as trailing 32-bit word:
            cmdLen = data_spec_constants.LEN2
            s1Reg  = 0
            paramsString = "%s, data = %d" %(paramsString, data)

        if src2Reg is not None:
            self.checkRegisterRange(src2Reg, "%s: source 2 register"%subOpcodeName)
            regUsage = regUsage | 0x1
            s2Reg    = src2Reg
            paramsString = "%s, src2Reg = %d" %(paramsString, s2Reg)
        elif twoSrcOperands is True:
            # Use immediate data, added as trailing 32-bit word:
            cmdLen = data_spec_constants.LEN2
            s2Reg  = 0
            paramsString = "%s, data = %d" %(paramsString, data)

        # Assemble command word and list of words (may include immediate data):
        cmdWord = (cmdLen<<28) | (opcode<<20) | (regUsage<<16)
        cmdWord = cmdWord | (dReg<<12) | (s1Reg<<8) | (s2Reg<<4) | (subOpcode)
        if cmdLen == data_spec_constants.LEN2:
            cmdWordList = [cmdWord, data]
        else:
            cmdWordList = [cmdWord]

        cmdString = "%s %s" % (subOpcodeName, paramsString)
        self.writeCommandToFiles(cmdWordList, cmdString)
        return

    """
    Commands to manipulate parameter structures
    """

    def copyStruct(self, destReg = None, destStruct = 0, \
                         src1Reg = None,  srcStruct = 0):
        """
        CMD_CODE: 0x70, COPY_STRUCT
        Overwrites the destination structure with an exact copy of
        the source structure. The IDs of the two structures can be
        supplied as immediate values or in registers.
        """
        # Check if a valid destination register has been specified:
        if destReg is not None:
            self.checkRegisterRange(destReg, "COPY_STRUCT: Destination register")
            regUsage  = 0x4
            destRegId = destReg
            paramString = "destStructReg = %d" % destReg
        else:
            regUsage  = 0x0
            if destStruct < 0  or destStruct > 15:
                errorString = "COPY_STRUCT - Destination struct ID (%d) " + \
                              "out of range 0->15." % destStruct
                self.raiseDsgSpecCmdException(errorString)
            destRegId = destStruct
            paramString = "destStructID = %d" % destStruct
        if src1Reg is not None:
            self.checkRegisterRange(src1Reg, "COPY_STRUCT: Source register")
            regUsage  = regUsage | 0x2
            src1RegId = src1Reg
            paramString = "%s, sourceStructReg = %d" % (paramString, src1Reg)
        else:
            if srcStruct < 0  or srcStruct > 15:
                errorString = "COPY_STRUCT - Source struct ID (%d) " + \
                              "out of range 0->15." % srcStruct
                self.raiseDsgSpecCmdException(errorString)
            src1RegId = srcStruct
            paramString = "%s, sourceStructID = %d" % (paramString, srcStruct)

        cmdWord = (data_spec_constants.LEN1<<28)| \
                  (data_spec_constants.DSG_COPY_STRUCT<<20) | (regUsage<<16) | \
                  (destRegId<<12) | (src1RegId<<8)
        cmdString = "COPY_STRUCT %s" % paramString
        self.writeCommandToFiles([cmdWord], cmdString)


    def copyParam(self, destStruct = None, destParam = 0, \
                         srcStruct = None,  srcParam = 0):
        """
        CMD_CODE: 0x71, COPY_PARAM
        Copies a parameter from one param structure to another.
        If not specified, parameter zero is assumed.
        """
        # Use register range checker to validate structure IDs
        # for source and destination structures:
        if destStruct is not None:
            self.checkRegisterRange(destStruct, "COPY_PARAM: Destination struct ID")
        else:
            errorString = "COPY_PARAM - Destination struct ID not specified."
            self.raiseDsgSpecCmdException(errorString)
        if srcStruct is not None:
            self.checkRegisterRange(srcStruct, "COPY_PARAM: Source struct ID")
        else:
            errorString = "COPY_PARAM - Source struct ID not specified."
            self.raiseDsgSpecCmdException(errorString)
        if destParam < 0 or destParam > 255:
            errorString = "COPY_PARAM - Destination parameter index (%d) " % destParam
            errorString = "%s not in range 0->255." % errorString
            self.raiseDsgSpecCmdException(errorString)
        if srcParam < 0 or srcParam > 255:
            errorString = "COPY_PARAM - Source parameter index (%d) " % srcParam
            errorString = "%s not in range 0->255." % errorString
            self.raiseDsgSpecCmdException(errorString)
        cmdWord1  = (data_spec_constants.LEN2<<28) | \
                    (data_spec_constants.DSG_COPY_PARAM<<20) | \
                    (destStruct<<12) | (srcStruct<<8)
        cmdWord2  = (destParam<<8)   | (srcParam)
        cmdString = "COPY_PARAM destParam = %d:%d, sourceParam = %d:%d" % \
                    (destStruct, destParam, srcStruct, srcParam)
        self.writeCommandToFiles([cmdWord1, cmdWord2], cmdString)

    def writeParam(self, destStruct = None, destParam = 0, \
                         srcReg = None,  data = 0):
        """
        CMD_CODE: 0x72, WRITE_PARAM
        """
        # Check destination structure information:
        if destStruct is not None:
            self.checkRegisterRange(destStruct, "WRITE_PARAM: Destination struct ID")
        else:
            errorString = "WRITE_PARAM - Destination struct ID not specified."
            self.raiseDsgSpecCmdException(errorString)
        if destParam < 0 or destParam > 255:
            errorString = "WRITE_PARAM - Destination parameter index (%d) " % destParam
            errorString = "%s not in range 0->255." % errorString
            self.raiseDsgSpecCmdException(errorString)
        paramString = "destination %d:%d" % (destStruct, destParam)
        # Check source information:
        if srcReg is not None:
            regUsage = 0x2
            regNum   = srcReg
            cmdLen = data_spec_constants.LEN1
            paramString = "%s, srcReg = %d" % (paramString, srcReg)
        else:
            regUsage = 0x0
            cmdLen   = data_spec_constants.LEN2
            regNum   = 0x0
            paramString = "%s, data = 0x%X" % (paramString, data)
        cmdWord = (cmdLen<<28) | \
                  (data_spec_constants.DSG_WRITE_PARAM<<20) | (regUsage<<16) | \
                  (destStruct<<12) | (regNum<<8)       | (destParam)
        if srcReg is not None:
            cmdWordList = [cmdWord]
        else:
            cmdWordList = [cmdWord, data]
        cmdString = "WRITE_PARAM %s" % paramString
        self.writeCommandToFiles(cmdWordList, cmdString)


    def writeParamComponent(self,                    dataReg = None,
                            srcStructReg = None, srcParamReg = None,
                             srcStructId = 0,     srcParamId = 0,
                           destStructId  = 0,    destParamId = 0,
                           destInsertLSB = 0,  destInsertLen = 1):
        """
        CMD_CODE: 0x73, WRITE_PARAM_COMPONENT
        Writes a bit range withint a parameter of one structure, given
        a data value either read from a register or a parameter from
        another structure.
        For the source, the user can provide a data value in a register,
        or chose to select a parameter from another structure. In this
        latter case, the IDs of the structure and paramater can either be
        hard-coded or themselves be given in registers.
        For the destination there is currently less flexibility. The IDs
        of the structure and paramater must be hard-coded, as well as
        the LSB of the inserted fragment and the number of inserted bits.
        """
        # Construct info for source parameters:
        if dataReg is not None:
            # User is providing the source data in a register:
            self.checkRegisterRange(dataReg, "WRITE_PARAM_COMPONENT:" +
                                                " Source data register")
            regUsage           = 0x4
            dataRegNum         = dataReg
            srcStructId_or_reg = 0x0
            srcParamId_or_reg  = 0x0
            paramString = "dataReg = %d" % dataReg
        else:
            # Source is provided by a parameter in a structure.
            dataRegNum = 0x0
            # Is the ID of this given as an immediate or in a register?
            if srcStructReg is not None:
                # It's given in a register, check it's a valid one:
                self.checkRegisterRange(srcStructReg, "WRITE_PARAM_COMPONENT:" +
                                                " Source structure register")
                regUsage = 0x2
                srcStructId_or_reg = srcStructReg
                paramString = "srcStructReg = %d" % srcStructReg
            else:
                # It's given as an immediate:
                regUsage = 0x0
                srcStructId_or_reg = srcStructId
                paramString = "srcStructId = %d" % srcStructId
            # Now check the paramater index for the source value:
            if srcParamReg is not None:
                # It's given in a register, check it's a valid one:
                self.checkRegisterRange(srcParamReg, "WRITE_PARAM_COMPONENT:" +
                                                " Source parameter register")
                regUsage = regUsage | 0x1
                srcParamId_or_reg = srcParamReg
                paramString = "%s, srcParamReg = %d" % (paramString, srcParamReg)
            else:
                # It's given as an immediate:
                srcParamId_or_reg = srcParamId
                paramString = "%s, srcParamId = %d" % (paramString, srcParamId)

        cmdWord = (data_spec_constants.LEN2<<28) | \
                  (data_spec_constants.DSG_WRITE_PARAM_COMPONENT<<20) | (regUsage<<16) | \
                  (dataRegNum<<12) | (srcStructId_or_reg<<8)   | (srcParamId_or_reg)

        # Construct info for destination parameters:
        # Structure ID:
        self.checkRegisterRange(destStructId, "WRITE_PARAM_COMPONENT:" +
                                        " Destination structure ID")
        # Parameter ID:
        self.checkRegisterRange(destParamId, "WRITE_PARAM_COMPONENT:" +
                                        " Destination parameter ID")
        # LSB and length fields:
        if destInsertLSB <0 or destInsertLSB>31:
            errorString = "WRITE_PARAMETER_COMPONENT: Insertion LSB (%d)"% destInsertLSB
            errorString = "%s not in range 0->31." % errorString
            self.raiseDsgSpecCmdException(errorString)
        if destInsertLen <0 or destInsertLen>31:
            errorString = "WRITE_PARAMETER_COMPONENT: Insertion length (%d)"% destInsertLen
            errorString = "%s not in range 0->31." % errorString
            self.raiseDsgSpecCmdException(errorString)

        destParamString = "destination %d:%d, insertLSB = %d, len = %d" % \
                          (destStructId, destParamId, destInsertLSB, destInsertLen)

        cmdWord2 = (destInsertLen<<26) | (destInsertLSB<<20) | \
                   (destStructId<<8)   | (destParamId)

        # Create the command and write it to file(s):
        cmdString = "WRITE_PARAM_COMPONENT %s, %s" % (paramString, destParamString)
        self.writeCommandToFiles([cmdWord, cmdWord2], cmdString)


    """
    Commands to print information to the screen/tubotron window:
    """

    def printVal(self, src1Reg = None, data = 0):
        """
        CMD_CODE: 0x80, PRINT_VAL
        Prints out a value, either a register or immediate, to the screen
        or sends it for display on the host.
        If a source 1 register is specified, it's value is used. If not,
        the immediate constant is used (not sure if this is useful!)
        """
        # Check if a valid register has been specified:
        if src1Reg is not None:
            self.checkRegisterRange(src1Reg, "PRINT_VAL: Source register")
            regUsage  = 0x2
            regId     = src1Reg
            cmdLen    = data_spec_constants.LEN1
            cmdString = "PRINT_VAL src1Reg = %d" % src1Reg
        else:
            regUsage  = 0x0
            regId     = 0x0
            cmdLen    = data_spec_constants.LEN2
            cmdString = "PRINT_VAL data = 0x%X" % data
        cmdWord = (cmdLen<<28) | (data_spec_constants.DSG_PRINT_VAL<<20) | \
                  (regUsage<<16) | (regId<<8)
        if src1Reg is not None:
            cmdWordList = [cmdWord]
        else:
            cmdWordList = [cmdWord, data]
        self.writeCommandToFiles(cmdWordList, cmdString)

    def printText(self, string = ""):
        """
        CMD_CODE: 0x81, PRINT_TXT
        """
        pass

    def printStruct(self, src1Reg = None, structId = 0):
        """
        CMD_CODE: 0x82, PRINT_STRUCT
        Prints the fields of one structure to the screen or sends
        them to the host for display.
        If source 1 register given, use its contents to select the
        struct to display. If not, use the immediate value, structId.
        """
        # Check if a valid register has been specified:
        if src1Reg is not None:
            self.checkRegisterRange(src1Reg, "PRINT_STRUCT: Source register")
            regUsage  = 0x2
            regId     = src1Reg
            immediate = 0x0
            cmdString = "PRINT_STRUCT src1Reg = %d" % src1Reg
        else:
            if structId < 0 or structId > 15:
                errorString = "PRINT_STRUCT - Given struct ID not in range 0->15."
                self.raiseDsgSpecCmdException(errorString)
            regUsage  = 0x0
            regId     = 0x0
            immediate = structId
            cmdString = "PRINT_STRUCT id = %d" % structId
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_PRINT_STRUCT<<20) | (regUsage<<16) | \
                  (regId<<8) | (immediate)
        self.writeCommandToFiles([cmdWord], cmdString)

    """
    Close Spec Cleanly
    """
    def endSpec(self):
        """
        CMD_CODE: 0xFF, END_SPEC
        Indicates to the SpecExecutor that this is the end of the Data Spec.
        """
        # Write blank line:
        cmdWordList = [] # Nothing appears in the binary file
        cmdString = "\nEnd of specification:"
        self.writeCommandToFiles(cmdWordList, cmdString, noInstructionNumber = True)

        # Write end-of-spec command:
        cmdWord = (data_spec_constants.LEN1<<28) | \
                  (data_spec_constants.DSG_END_SPEC<<20)
        cmdWordList = [cmdWord, -1]
        cmdString = "END_SPEC"
        self.writeCommandToFiles(cmdWordList, cmdString)
        
        if self.write_binary_specs and self.data_spec_exec is None:
            self.file_handle_bin.close()
        if self.write_text_specs:
            self.file_handle_txt.close()

    """
          ********* Common sub-routines used by most commands *********
    """

    def writeCommandToFiles(self, cmdWordList, cmdString, indent = False, \
                            outdent = False, noInstructionNumber = False):
        """
        Writes the binary command to the binary output file and, if the
        user has requested a text output for debug purposes, also write the
        text version to the text file.
        Setting the optional parameter 'indent' to True causes subsequent
        commands to be indented by two spaces relative to this one.
        Similarly, setting 'outdent' to True, reverses this spacing.
        """
        if self.write_binary_specs:
            words = numpy.array(cmdWordList, dtype="uint32")
            if self.data_spec_exec is None:
                words.tofile(self.file_handle_bin)
            elif len(words) > 0:
                self.data_spec_exec.call(words)
        
        if self.write_text_specs:
            if outdent is True:
                self.txt_indent -= 1
                if self.txt_indent < 0:
                    self.txt_indent = 0
            if noInstructionNumber is True:
                cmdString = "%s%s\n" % ("   "*self.txt_indent, cmdString)
            else:
                cmdString = "%#x. %s%s\n" % (self.instruction_counter, \
                                            "   "*self.txt_indent, cmdString)
                self.instruction_counter += len(cmdWordList)
            self.file_handle_txt.write(cmdString)
            if indent is True:
                self.txt_indent += 1
        return


    """
          ********* Format conversion functions for representing numbers *********
    """

    def doubleToS1615(self, myDouble):
        """
        Reformat a double into a 32-bit integer representing s1615 format
        (i.e. signed 16.15).
        Raise an exception if the value cannot be represented in this way.
        """
        if (myDouble < -65536.0) or (myDouble > (65536.0-1/32768.0)):
            raise exceptions.DsgFormatConversionError(\
            "ERROR: DSG - double cannot be recast as a s1615. Exiting.")

        # Shift up by 15 bits:
        scaledMyDouble = float(myDouble) * 32768.0

        # Round to an integer:
        # **THINK** should we actually round here?
        myS1615 = int(scaledMyDouble)
        return myS1615

    def doubleToS2111(self, myDouble):
        """
        Reformat a double into a 32-bit unsigned integer representing u2111 format
        (i.e. unsigned 21.11 - 32-bit extension of 5.11 used for STDP).
        Raise an exception if the value cannot be represented in this way.
        """
        if (myDouble < -2097152.0) or (myDouble >= 2097152.0):
            raise exceptions.DsgFormatConversionError(\
            "ERROR: DSG - double cannot be recast as a u2111. Exiting.")

        # Shift up by 11 bits:
        scaledMyDouble = float(myDouble) * 2048.0

        # Round to an integer:
        myS2111 = int(round(scaledMyDouble))
        return myS2111

    def doubleToS511(self, myDouble):
        """
        Reformat a double into a 16-bit unsigned integer representing u511 format
        (i.e. unsigned 5.11 used for STDP LUTs).
        Raise an exception if the value cannot be represented in this way.
        """
        if (myDouble < -31.0) or (myDouble >= 31.0):
            raise exceptions.DsgFormatConversionError(\
            "ERROR: DSG - double cannot be recast as a u2111. Exiting.")

        # Shift up by 11 bits:
        scaledMyDouble = float(myDouble) * 2048.0

        # Round to an integer:
        # **THINK** should we actually round here?
        myS511 = int(scaledMyDouble)
        return myS511


    def rescaleDoubleToU032(self, myDouble, minVal, maxVal):
        """
        Re-scales a double into a 32-bit integer representing u032 format
        (i.e. 0.32) given a min and max value for the variable. The output
        value then represents the fraction of the interval between the min
        and max values represented by the value.
        """
        if (maxVal <= minVal):
            raise exceptions.DsgFormatConversionError(\
            "ERROR: DSG - Re-scale double failed because maxVal <= minVal. Exiting.")
        # Obtain fraction of interval:
        frac = (myDouble - minVal*1.0)/(maxVal*1.0 - minVal*1.0)
        # Re-scale new value to be a 32-bit integer (multiply by 2^32):
        myU032 = ctypes.c_uint32(frac * 4294967296.0)
        return myU032


    """ *** Functions to support data type conversion *** """

    def translateDataType(self, dataTypeDescription):
        """
        Translate the textual data type description into a 5-bit
        value.
        """
        encodedDataType = self.dataTypes[dataTypeDescription]
        return encodedDataType

    def dataTypeIsSigned(self, dataType):
        """
        When passed a string representing a data type, returns
        '1' if the data type is signed and '0' if unsigned
        """
        isSigned = self.dataTypesSigned[dataType]
        return isSigned

    def dataTypeLength(self, dataType):
        """
        Returns the length of the data type, in bytes
        """
        dataLen = self.dataTypesLength[dataType]
        return dataLen

    def cropDataWord(self, dataType, dataValue):
       """
       Produce appropriate sign extended (or zero extended) data value on 32-bits
       given a 32-bit input value and data type (which may be 8-bit, 16-bit or
       32-bit)
       """
       isSigned = self.dataTypeIsSigned(dataType)
       dataLen  = self.dataTypeLength(dataType)
       signBit = 0
       modifiedDataValue = dataValue
       if isSigned == 1:
         if dataLen == 1:
           signBit = (dataValue >> 7)&0x1
           if signBit == 1:
             modifiedDataValue = dataValue | 0xFFFFFF00
           else:
             modifiedDataValue = dataValue & 0xFF
         elif dataLen == 2:
           signBit = (dataValue >> 15)&0x1
           modifiedDataValue = dataValue | 0xFFFF0000
       else:   # Unsigned:
         if dataLen == 1:
           modifiedDataValue = dataValue & 0xFF
         elif dataLen == 2:
           modifiedDataValue = dataValue & 0xFFFF
       return modifiedDataValue

    """ *** Methods to raise exceptions during spec generation *** """

    def checkRegisterRange(self, regNum, useString):
        """
        Short-hand routine to check that a register is in range (this is
        widely used in command parsing). The correct range is 0->15 for valid
        registers.  Failing the range check triggers a Spec Cmd exception.
        The use string includes the command name and the purpose of the
        register, e.g. "LOOP: Count register" and is displayed in the exception
         message if the register is out of range.
        """
        if regNum<0 or regNum>15:
            errorString = "%s (%d)" % (useString, regNum)
            errorString = "%s out of range 0->15." % errorString
            self.raiseDsgSpecCmdException(errorString)

    def raiseDsgSpecCmdException(self, errorString):
        """
        Raises a standard exception signlling a problem with the execution of a Spec
        command. It also provides information of where the error occurred.
        """
        logger.error("*****************************************************")
        logger.error("      ***** ERROR during Spec Generation ****")
        logger.error(errorString)
        logger.error("*****************************************************\n")
        errorStr = "Problem occurred while generating command # %d of file:\n%s\n" % \
              (self.instruction_counter, self.file_name)
        logger.error(errorStr)
        raise exceptions.DsgSpecCmdException()

