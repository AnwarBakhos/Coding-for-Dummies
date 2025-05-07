import sys
import os
import re

op_codes = {
    "YOLOAD": "0001",
    "ADD": "0010",
    "GREATERTHAN": "0011",
    "YEET": "0100",
    "YOLO": "0101",
    "SAMEBRO": "0110",
    "MODULOIZE": "0111",
    "INCREMENT": "1000",
    "YELLSTR": "1001",
    "YELLVAL": "1010",
    "HALT": "1111",
    "NOTGREATEROREQUAL": "1100"
}

registers = {f"R{i}": f"{i:03b}" for i in range(8)}

def assemble(asm_file: str, outfile_path: str, op_codes, registers):
    labels = {}
    string_table = {}
    instructions = []
    address = 0
    machine_code = []

    # First Pass: Collect labels and string literals
    try:
        with open(asm_file, "r") as infile:
            for line_num, line in enumerate(infile):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if not parts:
                    continue

                op_code = parts[0]

                if op_code.endswith(":"):
                    label = op_code[:-1]
                    labels[label] = address
                elif op_code.startswith(".STRING"):
                    label = parts[0]
                    literal = " ".join(parts[1:]).strip().strip('"')
                    string_table[label] = literal
                else:
                    instructions.append(line)
                    address += 2 # Assume each instruction is 2 bytes

    except FileNotFoundError:
        print(f"Error: Input file '{asm_file}' not found.")
        return

    # Second Pass: Assemble instructions
    for instruction in instructions:
        parts = instruction.split()
        op_code = parts[0]
        binary_instruction = ""

        if op_code in op_codes:
            binary_instruction += op_codes[op_code]

            if op_code == "YOLOAD":
                match = re.match(r"YOLOAD\s+(R\d+),\s*(\d+)\(R0\)", instruction)
                if match:
                    dest_reg_str = match.group(1)
                    immediate_str = match.group(2)
                    dest_reg_bin = registers.get(dest_reg_str)
                    try:
                        immediate = int(immediate_str)
                        binary_instruction += dest_reg_bin + "000" + f"{immediate:06b}"
                    except ValueError:
                        print(f"Error: Invalid immediate value '{immediate_str}' in line: {instruction}")
                        continue
                else:
                    print(f"Error: Invalid YOLOAD format in line: {instruction}")
                    continue

            elif op_code == "ADD":
                dest_reg_str, src1_reg_str, src2_reg_str = [reg.replace(",", "").strip() for reg in parts[1:]]
                binary_instruction += registers.get(dest_reg_str) + registers.get(src1_reg_str) + registers.get(src2_reg_str) + "000"

            elif op_code == "GREATERTHAN":
                reg1_str, reg2_str, label = [part.replace(",", "").strip() for part in parts[1:]]
                binary_instruction += registers.get(reg1_str) + registers.get(reg2_str) + f"{labels.get(label, 0):010b}"

            elif op_code in ["YEET", "YOLO"]:
                label = parts[1].strip()
                binary_instruction += "000" + "000" + f"{labels.get(label, 0):010b}"

            elif op_code == "SAMEBRO":
                reg1_str, reg2_str, label = [part.replace(",", "").strip() for part in parts[1:]]
                binary_instruction += registers.get(reg1_str) + registers.get(reg2_str) + f"{labels.get(label, 0):010b}"

            elif op_code == "MODULOIZE":
                dest_reg_str, src_reg_str, mod_reg_str = [reg.replace(",", "").strip() for reg in parts[1:]]
                binary_instruction += registers.get(dest_reg_str) + registers.get(src_reg_str) + registers.get(mod_reg_str) + "000"

            elif op_code == "INCREMENT":
                reg_str = parts[1].strip()
                binary_instruction += registers.get(reg_str) + "00000000000"

            elif op_code == "YELLSTR":
                label = parts[1].strip()
                string_index = list(string_table.keys()).index(label) if label in string_table else 0
                binary_instruction += "000" + "000" + f"{string_index:010b}"

            elif op_code == "YELLVAL":
                reg_str = parts[1].strip()
                binary_instruction += registers.get(reg_str) + "00000000000"

            elif op_code == "HALT":
                binary_instruction += "0000000000000000"

            elif op_code == "NOTGREATEROREQUAL":
                reg1_str, reg2_str, label = [part.replace(",", "").strip() for part in parts[1:]]
                binary_instruction += registers.get(reg1_str) + registers.get(reg2_str) + f"{labels.get(label, 0):010b}"

            if binary_instruction:
                machine_code.append(binary_instruction)

    try:
        with open(outfile_path, "w") as outfile:
            for code in machine_code:
                outfile.write(code + "\n")
        print(f"Assembled '{asm_file}' -> '{outfile_path}'")
    except Exception as e:
        print(f"Error writing to output file '{outfile_path}': {e}")

if __name__ == "__main__":
    asm_files = ["addition.asm", "conditional.asm", "fizzbuzz.asm"]
    for asm_file in asm_files:
        mc_file = asm_file.replace(".asm", ".mc")
        assemble(asm_file, mc_file, op_codes, registers)