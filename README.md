# VLAN Replacer

A Python tool for replacing VLAN IDs in Fortigate configuration files with support for both range-based and individual VLAN mappings.

## Features

- **Range-based replacement**: Replace continuous VLAN ranges with 1:1 correlation (e.g., 100-200 → 500-600)
- **Individual VLAN mappings**: Replace specific VLANs using a JSON mapping file (e.g., 160 → 2500, 405 → 2501)
- **Combined mode**: Use both methods together, with individual mappings taking precedence
- **Detailed reporting**: See exactly which VLANs were replaced and which were not found
- **Safe processing**: Creates a new output file, never modifies the original

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Installation

1. Clone or download this repository:

   ```bash
   git clone <repository-url>
   cd vlan-replacer
   ```

2. Verify Python is installed:
   ```bash
   python3 --version
   ```

## Usage

### Basic Syntax

```bash
python3 vlan-replacer.py <input_file> [OPTIONS]
```

### Option 1: Range-based Replacement

Replace a continuous range of VLANs with a new range (1:1 correlation):

```bash
python3 vlan-replacer.py fortigate.conf --old-range 100 200 --new-range 500 600
```

This replaces:

- VLAN 100 → 500
- VLAN 101 → 501
- ...
- VLAN 200 → 600

### Option 2: Individual VLAN Mappings

Create a JSON file with specific VLAN mappings:

**vlan-mappings.json:**

```json
{
  "160": 2500,
  "405": 2501,
  "667": 2508,
  "409": 1111
}
```

Run the replacement:

```bash
python3 vlan-replacer.py fortigate.conf --mapping-file vlan-mappings.json
```

### Option 3: Combined Mode

Use both range-based and individual mappings together. Individual mappings take precedence:

```bash
python3 vlan-replacer.py fortigate.conf --old-range 100 200 --new-range 500 600 --mapping-file vlan-mappings.json
```

**Example scenario:**

- Mapping file contains: `{"160": 2500}`
- Range: 100-200 → 500-600

Result:

- VLAN 160 → 2500 (from mapping file - takes precedence)
- VLAN 100 → 500 (from range)
- VLAN 151 → 551 (from range)

### Specifying Output File

By default, the output file is named `<input>-modified.<ext>`. You can specify a custom output file:

```bash
python3 vlan-replacer.py fortigate.conf -o new-fortigate.conf --old-range 100 200 --new-range 500 600
```

### Command-Line Options

| Option                  | Description                                      |
| ----------------------- | ------------------------------------------------ |
| `input_file`            | Input Fortigate configuration file (required)    |
| `-o`, `--output`        | Output file (default: `input_file-modified.ext`) |
| `--old-range START END` | Old VLAN range to replace (e.g., 100 200)        |
| `--new-range START END` | New VLAN range to use (e.g., 500 600)          |
| `--mapping-file FILE`   | JSON file with individual VLAN mappings          |

**Note:** You must provide either `--mapping-file` or both `--old-range` and `--new-range` (or all three for combined mode).

## Examples

### Example 1: Simple Range Replacement

```bash
python3 vlan-replacer.py fortigate.conf --old-range 100 200 --new-range 500 600
```

### Example 2: Individual Mappings Only

**vlan-mappings.json:**

```json
{
  "160": 2500,
  "405": 2501,
  "667": 2508
}
```

```bash
python3 vlan-replacer.py fortigate.conf --mapping-file vlan-mappings.json
```

### Example 3: Combined with Custom Output

```bash
python3 vlan-replacer.py fortigate.conf \
  --old-range 100 200 \
  --new-range 500 600 \
  --mapping-file vlan-mappings.json \
  -o new-fortigate.conf
```

## Output Report

The tool provides detailed reports showing:

1. **Total replacements made**
2. **Individual mappings applied** (if using mapping file)
3. **Range-based replacements** (if using ranges)
4. **VLANs not found** in the config file (for both mappings and ranges)

## JSON Mapping File Format

The mapping file must be valid JSON with VLAN IDs as keys:

```json
{
  "old_vlan_1": new_vlan_1,
  "old_vlan_2": new_vlan_2,
  "old_vlan_3": new_vlan_3
}
```

**Important:**

- Keys must be valid VLAN IDs (strings)
- Values must be valid VLAN IDs (integers)
- Valid VLAN range: 1-4094

### Valid Examples

```json
{
  "100": 2000,
  "101": 2001,
  "150": 3500
}
```

## How It Works

1. The tool reads your Fortigate configuration file
2. It searches for all `set vlanid XXX` patterns
3. For each VLAN found:
   - First checks if it's in the individual mapping file (if provided)
   - Then checks if it's in the specified range (if provided)
   - Replaces with the new VLAN ID if matched
   - Keeps the original if no match
4. Writes the modified configuration to the output file
5. Displays a detailed report of all changes

## Safety Features

- **Non-destructive**: Never modifies the original file
- **Validation**: Checks that range sizes match before processing
- **Error handling**: Clear error messages for invalid inputs
- **Detailed reporting**: Shows exactly what was changed and what wasn't found

## Troubleshooting

### Error: "Range size mismatch"

Both ranges must have the same number of VLANs:

- **Y** Old: 100-199 (100 VLANs), New: 2000-2099 (100 VLANs)
- **N** Old: 100-199 (100 VLANs), New: 2000-2199 (200 VLANs)

### Error: "Invalid JSON in mapping file"

Ensure your JSON file is properly formatted:

- Use double quotes for keys
- No trailing commas
- Valid JSON syntax

### Error: "Must provide either --mapping-file or --old-range/--new-range"

You need to specify at least one replacement method.

## Contributing

Contributions and improvements are welcome! Feel free to submit issues or pull requests.

## Changelog

### Version 1.0

- Individual VLAN mapping support via JSON files
- Range-based VLAN replacement
- Combined mode (mappings + ranges)
- Reporting for VLANs not found in config
