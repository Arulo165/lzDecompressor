"""
Standalone LZ77 Decompressor
Decompresses LZ77-compressed files and saves them
"""

import sys
import os
from pathlib import Path


def GetUncompressedSize(inData):
    """Gets the uncompressed size from the LZ77 header"""
    offset = 4
    outSize = inData[1] | (inData[2] << 8) | (inData[3] << 16)

    if not outSize:
        outSize = inData[4] | (inData[5] << 8) | (inData[6] << 16) | (inData[7] << 24)
        offset += 4

    return outSize, offset


def UncompressLZ77(inData):
    """Decompresses LZ77-compressed data"""
    if inData[0] != 0x11:
        print("[!] Warning: File does not start with 0x11. May not be LZ77-compressed.")
        return inData

    inLength = len(inData)
    outLength, offset = GetUncompressedSize(inData)
    outData = bytearray(outLength)

    outIndex = 0

    while outIndex < outLength and offset < inLength:
        flags = inData[offset]
        offset += 1

        for x in reversed(range(8)):
            if outIndex >= outLength or offset >= inLength:
                break

            if flags & (1 << x):
                first = inData[offset]
                offset += 1

                second = inData[offset]
                offset += 1

                if first < 32:
                    third = inData[offset]
                    offset += 1

                    if first >= 16:
                        fourth = inData[offset]
                        offset += 1

                        pos = (((third & 0xF) << 8) | fourth) + 1
                        copylen = ((second << 4) | ((first & 0xF) << 12) | (third >> 4)) + 273

                    else:
                        pos = (((second & 0xF) << 8) | third) + 1
                        copylen = (((first & 0xF) << 4) | (second >> 4)) + 17

                else:
                    pos = (((first & 0xF) << 8) | second) + 1
                    copylen = (first >> 4) + 1

                for y in range(copylen):
                    outData[outIndex + y] = outData[outIndex - pos + y]

                outIndex += copylen

            else:
                outData[outIndex] = inData[offset]
                offset += 1
                outIndex += 1

    return bytes(outData)


def decompress_file(input_path, output_path=None):
    """
    Decompresses an LZ77 file and saves it
    
    Args:
        input_path: Path to the compressed input file
        output_path: Path to the output file (optional)
    
    Returns:
        True on success, False on error
    """
    try:
        print(f"[*] Reading file: {input_path}")
        with open(input_path, 'rb') as f:
            compressed_data = f.read()
        
        print(f"[*] Input size: {len(compressed_data)} bytes")
        
        print("[*] Decompressing...")
        decompressed_data = UncompressLZ77(compressed_data)
        
        print(f"[*] Output size: {len(decompressed_data)} bytes")
        
        if output_path is None:
            input_file = Path(input_path)
            if input_file.suffix.lower() == '.lz':
                output_path = str(input_file.with_suffix(''))
            else:
                output_path = input_path + '.dec'
        
        print(f"[*] Saving to: {output_path}")
        with open(output_path, 'wb') as f:
            f.write(decompressed_data)
        
        print(f"[✓] Successfully decompressed!")
        return True
        
    except FileNotFoundError:
        print(f"[!] Error: Input file not found: {input_path}")
        return False
    except Exception as e:
        print(f"[!] Error during decompression: {e}")
        return False


def decompress_folder(input_folder, output_folder):
    """
    Decompresses all LZ77 files in a folder recursively
    
    Args:
        input_folder: Path to the input folder
        output_folder: Path to the output folder
    
    Returns:
        Number of successfully decompressed files
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Scanning folder: {input_folder}")
    
    decompressed_count = 0
    
    for lz_file in input_path.rglob('*.lz'):
        
        relative_path = lz_file.relative_to(input_path)
        output_file = output_path / relative_path.with_suffix('')
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"[*] Decompressing: {relative_path}")
        
        if decompress_file(str(lz_file), str(output_file)):
            decompressed_count += 1
    
    print(f"\n[✓] {decompressed_count} file(s) decompressed!")
    return decompressed_count


def main():
    """Main function with interactive input"""
    print("=" * 60)
    print("LZ77 Decompressor - Standalone Decompression Program")
    print("=" * 60)
    print()
    
    while True:
        input_path_str = input("Enter the path to the compressed file or folder (or 'exit' to quit): ").strip()
        
        if input_path_str.lower() == 'exit':
            print("[*] Program terminated.")
            break
        
        if not input_path_str:
            print("[!] Error: No path entered!")
            continue
        
        input_path = Path(input_path_str)
        script_dir = Path(__file__).parent
        
        if input_path.is_dir():
            output_folder = script_dir / input_path.name
            print(f"[*] Detected: Folder")
            print(f"[*] Output folder: {output_folder}")
            decompress_folder(str(input_path), str(output_folder))
            
        elif input_path.is_file():
            if input_path.suffix.lower() == '.lz':
                output_filename = input_path.stem
            else:
                output_filename = input_path.name + '.dec'
            
            output_file = script_dir / output_filename
            decompress_file(str(input_path), str(output_file))
        else:
            print(f"[!] Error: Path not found: {input_path}")
        
        print()


if __name__ == '__main__':
    main()

