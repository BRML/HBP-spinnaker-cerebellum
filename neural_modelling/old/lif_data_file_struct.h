

struct
{
  int dsg_magic_num = 0x0AD6_AD13;
  int spec_exec_version = 0x0001_0000;
  int reserved0 = 0;
  int reserved1 = 0;

  int memRegionStartAddr[16]; // Start addresses, relative to base of this file

} region_0_header;

struct
{
  int recording_info; // Flags indicating what data to keep
} region_1_system;

struct
{
  int min_v; // Minimum voltage, in s1615 format
  int max_v; // Maximum voltage, in s1615 format
  int min_i; // Minimum current, in s1615 format
  int max_i; // Maximum current, in s1615 format
  int min_t; // Minimum time constant, in s1615 format
  int max_t; // Maximum time constant, in s1615 format

  int pop_id; // x<<24 | y<<15 | (proc-1)<<11
  int numNeurons;
  int numParams;
  int h;      // Time-step in micro-seconds

  int paramAddr[numParams]; // Start address of each param.
  int param1[numNeurons];   // Values of 1st param, one per neuron
  int param2[numNeurons];   // Values of 2nd param, one per neuron
  ...
  int paramN[numNeurons];   // Values of nth param, one per neuron
  
} region_2_neuron_params;

struct
{
  int row_len0;
  int row_len1;
  int row_len2;
  int row_len3;
  int row_len4;
  int row_len5;
  int row_len6;
  int row_len7;
} region_3_row_trans_table;

struct
{
  short synapticBlock[8 * 8 * 18];

} region_4_master_population_table;


struct
{
  synapticRow rows[numIncomingAxons];  // One row per arriving input in this bundle

} region_5_synaptic_matrix;

struct
{
  int synapsesInThisRow; // Number of valid entries.
  int numRows;           // Temp. Equal to numIncomingAxons.
  int synapse[maxSynapsesPerRowForThisBlock];
} synapticRow;

// Synapse struct:
// Bits 31:16 - Weight << 4
// Bits 15:14 - Reserved
// Bits 13:9  - Delay
// Bit   8    - Inhibtory
// Bits 7:0   - Index


