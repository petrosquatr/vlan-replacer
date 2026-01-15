import re
import sys
import argparse
import json
from pathlib import Path

def replace_vlan_ids(input_file, output_file, old_start=None, old_end=None, new_start=None, new_end=None, mapping_dict=None):
    """
    Replace VLAN IDs using individual mappings and/or range-based replacement.
    Individual mappings take precedence over range-based replacements.
    
    Args:
        mapping_dict: Dictionary of {old_vlan: new_vlan} for individual replacements
        old_start, old_end: Range of old VLANs to replace
        new_start, new_end: Range of new VLANs to use
    """
    # Validate that at least one replacement method is provided
    has_ranges = all([old_start is not None, old_end is not None, new_start is not None, new_end is not None])
    has_mapping = mapping_dict is not None and len(mapping_dict) > 0
    
    if not has_ranges and not has_mapping:
        print("Error: Must provide either --mapping-file or --old-range/--new-range")
        return False
    
    # Validate ranges if provided
    offset = None
    if has_ranges:
        if old_start >= old_end:
            print(f"Error: Old range start ({old_start}) must be less than end ({old_end})")
            return False
        
        if new_start >= new_end:
            print(f"Error: New range start ({new_start}) must be less than end ({new_end})")
            return False
        
        old_range_size = old_end - old_start + 1
        new_range_size = new_end - new_start + 1
        
        if old_range_size != new_range_size:
            print(f"Error: Range size mismatch!")
            print(f"  Old range: {old_start}-{old_end} ({old_range_size} VLANs)")
            print(f"  New range: {new_start}-{new_end} ({new_range_size} VLANs)")
            print(f"  Both ranges must have the same number of VLANs for 1:1 replacement")
            return False
        
        # Calculate offset
        offset = new_start - old_start
    
    print(f"Reading configuration from: {input_file}")
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found!")
        return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Track replacements
    replacements = {}
    mapping_replacements = {}
    range_replacements = {}
    
    def replace_vlan(match):
        """Callback function to replace VLAN IDs"""
        vlan_id = int(match.group(1))
        
        # Priority 1: Check individual mapping (takes precedence)
        if has_mapping and vlan_id in mapping_dict:
            new_vlan_id = mapping_dict[vlan_id]
            replacements[vlan_id] = new_vlan_id
            mapping_replacements[vlan_id] = new_vlan_id
            return f"set vlanid {new_vlan_id}"
        
        # Priority 2: Check range-based replacement
        if has_ranges and old_start <= vlan_id <= old_end:
            new_vlan_id = vlan_id + offset
            replacements[vlan_id] = new_vlan_id
            range_replacements[vlan_id] = new_vlan_id
            return f"set vlanid {new_vlan_id}"
        
        # Keep original VLAN ID if no match
        return match.group(0)
    
    # Use regex to find and replace "set vlanid XXX" patterns
    # Pattern matches "set vlanid" followed by one or more digits
    pattern = r'set vlanid (\d+)'
    new_content = re.sub(pattern, replace_vlan, content)
    
    # Write to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"\nConfiguration written to: {output_file}")
    except Exception as e:
        print(f"Error writing file: {e}")
        return False
    
    # Print summary
    if replacements:
        print(f"\nTotal replacements: {len(replacements)} VLAN IDs")
        
        if mapping_replacements:
            print(f"\nIndividual mappings applied: {len(mapping_replacements)}")
            items = sorted(mapping_replacements.items())
            if len(items) <= 10:
                for old_vlan, new_vlan in items:
                    print(f"  {old_vlan} -> {new_vlan}")
            else:
                for old_vlan, new_vlan in items[:10]:
                    print(f"  {old_vlan} -> {new_vlan}")
                print(f"  ... and {len(items) - 10} more")
            
            # Show VLANs in mapping file that were not found
            if has_mapping:
                expected_vlans = set(mapping_dict.keys())
                found_vlans = set(mapping_replacements.keys())
                missing_vlans = sorted(expected_vlans - found_vlans)
                
                if missing_vlans:
                    print(f"\nVLANs in mapping file not found in config: {len(missing_vlans)}")
                    if len(missing_vlans) <= 20:
                        print(f"  {', '.join(map(str, missing_vlans))}")
                    else:
                        print(f"  {', '.join(map(str, missing_vlans[:10]))}, ... {', '.join(map(str, missing_vlans[-10:]))}")
        
        if range_replacements:
            print(f"\nRange-based replacements: {len(range_replacements)}")
            items = sorted(range_replacements.items())
            if len(items) <= 10:
                for old_vlan, new_vlan in items:
                    print(f"  {old_vlan} -> {new_vlan}")
            else:
                print("First 10:")
                for old_vlan, new_vlan in items[:10]:
                    print(f"  {old_vlan} -> {new_vlan}")
                print(f"  ... ({len(items) - 20} more replacements)")
                print("Last 10:")
                for old_vlan, new_vlan in items[-10:]:
                    print(f"  {old_vlan} -> {new_vlan}")
            
            # Show VLANs in range that were not found
            if has_ranges:
                expected_vlans = set(range(old_start, old_end + 1))
                found_vlans = set(range_replacements.keys())
                missing_vlans = sorted(expected_vlans - found_vlans)
                
                if missing_vlans:
                    print(f"\nVLANs in range {old_start}-{old_end} not found in config: {len(missing_vlans)}")
                    if len(missing_vlans) <= 20:
                        print(f"  {', '.join(map(str, missing_vlans))}")
                    else:
                        print(f"  {', '.join(map(str, missing_vlans[:10]))}, ... {', '.join(map(str, missing_vlans[-10:]))}")
    else:
        print("\nNo VLAN IDs were replaced.")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Replace VLAN IDs in Fortigate configuration files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Range-based replacement: Replace VLANs 100-200 with 500-600
  python3 vlan-replacer.py fortigate.conf --old-range 100 200 --new-range 500 600
  
  # Individual mappings: Use a JSON mapping file
  python3 vlan-replacer.py fortigate.conf --mapping-file vlan-mappings.json
  
  # Combined: Individual mappings take precedence over ranges
  python3 vlan-replacer.py fortigate.conf --old-range 100 200 --new-range 500 600 --mapping-file vlan-mappings.json
  
  # Specify output file
  python3 vlan-replacer.py fortigate.conf -o new-fortigate.conf --mapping-file vlan-mappings.json
        """)
    
    parser.add_argument('input_file', 
                        help='Input Fortigate configuration file')
    
    parser.add_argument('-o', '--output', 
                        dest='output_file',
                        help='Output file (default: input_file-modified.ext)')
    
    parser.add_argument('--mapping-file', 
                        type=str,
                        help='JSON file with individual VLAN mappings (e.g., {"151": 2500, "148": 2501})')
    
    parser.add_argument('--old-range', 
                        nargs=2, 
                        type=int,
                        metavar=('START', 'END'),
                        help='Old VLAN range to replace (e.g., 100 200)')
    
    parser.add_argument('--new-range', 
                        nargs=2, 
                        type=int,
                        metavar=('START', 'END'),
                        help='New VLAN range to use (e.g., 500 600)')
    
    args = parser.parse_args()
    
    # Extract values
    input_file = args.input_file
    
    # Validate that at least one method is provided
    if not args.mapping_file and not (args.old_range and args.new_range):
        parser.error("Must provide either --mapping-file or both --old-range and --new-range")
    
    # Validate that both range arguments are provided together
    if (args.old_range and not args.new_range) or (args.new_range and not args.old_range):
        parser.error("Both --old-range and --new-range must be provided together")
    
    # Load mapping file if provided
    mapping_dict = None
    if args.mapping_file:
        mapping_file_path = Path(args.mapping_file)
        if not mapping_file_path.exists():
            print(f"Error: Mapping file '{args.mapping_file}' not found!")
            sys.exit(1)
        
        try:
            with open(mapping_file_path, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
            
            # Convert string keys to integers
            mapping_dict = {int(k): int(v) for k, v in mapping_data.items()}
            print(f"Loaded {len(mapping_dict)} individual VLAN mappings from: {args.mapping_file}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in mapping file: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: Invalid VLAN IDs in mapping file (must be integers): {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading mapping file: {e}")
            sys.exit(1)
    
    # Extract range values if provided
    old_start = old_end = new_start = new_end = None
    offset = None
    if args.old_range and args.new_range:
        old_start, old_end = args.old_range
        new_start, new_end = args.new_range
        offset = new_start - old_start
    
    # Generate output filename if not provided
    if args.output_file:
        output_file = args.output_file
    else:
        base, ext = input_file.rsplit('.', 1) if '.' in input_file else (input_file, 'conf')
        output_file = f"{base}-modified.{ext}"
    
    # ASCII Art Header
    print("\n")
    print("=" * 70)
    print()
    print("  ╦  ╦╦  ╔═╗╔╗╔  ╦═╗╔═╗╔═╗╦  ╔═╗╔═╗╔═╗╦═╗")
    print("  ╚╗╔╝║  ╠═╣║║║  ╠╦╝║╣ ╠═╝║  ╠═╣║  ║╣ ╠╦╝")
    print("   ╚╝ ╩═╝╩ ╩╝╚╝  ╩╚═╚═╝╩  ╩═╝╩ ╩╚═╝╚═╝╩╚═")
    print()
    print("=" * 70)
    print("\n")
    print("=" * 60)
    print("  Fortigate Configuration VLAN ID Replacement Tool")
    print("=" * 60)
    
    if mapping_dict:
        print(f"Individual mappings: {len(mapping_dict)} VLANs")
    
    if args.old_range and args.new_range:
        print(f"Old range: {old_start}-{old_end} ({old_end - old_start + 1} VLANs)")
        print(f"New range: {new_start}-{new_end} ({new_end - new_start + 1} VLANs)")
        print(f"Offset: +{offset}" if offset >= 0 else f"Offset: {offset}")
    
    if mapping_dict and args.old_range:
        print("\nMode: Combined (individual mappings take precedence)")
    
    print("=" * 60)
    
    success = replace_vlan_ids(input_file, output_file, old_start, old_end, new_start, new_end, mapping_dict)
    
    if success:
        print("\n" + "=" * 60)
        print("Replacement completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Replacement failed!")
        print("=" * 60)
        sys.exit(1)
