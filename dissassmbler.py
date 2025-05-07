import sys
import os
import re

op_codes_reverse = {
    "0001": "YOLOAD",
    "0010": "ADD",
    "0011": "GREATERTHAN",
    "0100": "YEET",
    "0101": "YOLO",
    "0110": "SAMEBRO",
    "0111": "MODULOIZE",
    "1000": "INCREMENT",
    "1001": "YELLSTR",
    "1010": "YELLVAL",
    "1111": "HALT",
    "1100": "NOTGREATEROREQUAL"
}

registers_reverse = {f"{i:03b}": f"R{i}" for i in range(8)}

def disassemble(mc_file: str, outfile_path: str):
    try:
        with open(mc_file, "r") as infile:
            machine_code_lines = [line.strip() for line in infile if line.strip()]
    except FileNotFoundError:
        print(f"Error: Input file '{mc_file}' not found.")
        return

    assembly_lines = []
    string_literals_discovered = {}
    string_literal_counter = 0
    instruction_address = 0

    # First Pass: Identify potential label targets (for jumps/branches)
    label_targets = set()
    for instruction_code in machine_code_lines:
        opcode = instruction_code[0:4]
        if opcode in ["0011", "0100", "0101", "0110", "1100"]:  # Instructions with a label/address
            label_address_bin = instruction_code[7:]
            # While we don't know the actual label name yet, we mark the target address
            try:
                label_target = int(label_address_bin, 2) * 2 # Assuming each instruction is 2 bytes
                label_targets.add(label_target)
            except ValueError:
                pass # Handle potential errors in binary conversion

    # Second Pass: Disassemble instructions
    address_to_label = {}
    current_address = 0
    for instruction_code in machine_code_lines:
        opcode = instruction_code[0:4]
        asm_instruction = ""

        if current_address in label_targets and current_address not in address_to_label:
            new_label = f"LABEL_{len(address_to_label)}"
            assembly_lines.append(f"{new_label}:")
            address_to_label[current_address] = new_label

        if opcode in op_codes_reverse:
            instruction_name = op_codes_reverse[opcode]
            asm_instruction += instruction_name

            if instruction_name == "YOLOAD":
                dest_reg_bin = instruction_code[4:7]
                immediate_bin = instruction_code[10:16]
                dest_reg = registers_reverse.get(dest_reg_bin, "UNKNOWN")
                immediate = int(immediate_bin, 2)
                asm_instruction += f" {dest_reg}, {immediate}(R0)"
            elif instruction_name == "ADD":
                dest_reg_bin = instruction_code[4:7]
                src1_reg_bin = instruction_code[7:10]
                src2_reg_bin = instruction_code[10:13]
                dest_reg = registers_reverse.get(dest_reg_bin, "UNKNOWN")
                src1_reg = registers_reverse.get(src1_reg_bin, "UNKNOWN")
                src2_reg = registers_reverse.get(src2_reg_bin, "UNKNOWN")
                asm_instruction += f" {dest_reg}, {src1_reg}, {src2_reg}"
            elif instruction_name == "GREATERTHAN":
                reg1_bin = instruction_code[4:7]
                reg2_bin = instruction_code[7:10]
                label_address_bin = instruction_code[10:]
                reg1 = registers_reverse.get(reg1_bin, "UNKNOWN")
                reg2 = registers_reverse.get(reg2_bin, "UNKNOWN")
                try:
                    label_target_address = int(label_address_bin, 2) * 2
                    label = address_to_label.get(label_target_address, f"LABEL_TARGET_{label_target_address // 2}")
                    asm_instruction += f" {reg1}, {reg2}, {label}"
                except ValueError:
                    asm_instruction += f" {reg1}, {reg2}, UNKNOWN_LABEL"
            elif instruction_name in ["YEET", "YOLO"]:
                label_address_bin = instruction_code[7:]
                try:
                    label_target_address = int(label_address_bin, 2) * 2
                    label = address_to_label.get(label_target_address, f"LABEL_TARGET_{label_target_address // 2}")
                    asm_instruction += f" {label}"
                except ValueError:
                    asm_instruction += " UNKNOWN_LABEL"
            elif instruction_name == "SAMEBRO":
                reg1_bin = instruction_code[4:7]
                reg2_bin = instruction_code[7:10]
                label_address_bin = instruction_code[10:]
                reg1 = registers_reverse.get(reg1_bin, "UNKNOWN")
                reg2 = registers_reverse.get(reg2_bin, "UNKNOWN")
                try:
                    label_target_address = int(label_address_bin, 2) * 2
                    label = address_to_label.get(label_target_address, f"LABEL_TARGET_{label_target_address // 2}")
                    asm_instruction += f" {reg1}, {reg2}, {label}"
                except ValueError:
                    asm_instruction += f" {reg1}, {reg2}, UNKNOWN_LABEL"
            elif instruction_name == "MODULOIZE":
                dest_reg_bin = instruction_code[4:7]
                src_reg_bin = instruction_code[7:10]
                mod_reg_bin = instruction_code[10:13]
                dest_reg = registers_reverse.get(dest_reg_bin, "UNKNOWN")
                src_reg = registers_reverse.get(src_reg_bin, "UNKNOWN")
                mod_reg = registers_reverse.get(mod_reg_bin, "UNKNOWN")
                asm_instruction += f" {dest_reg}, {src_reg}, {mod_reg}"
            elif instruction_name == "INCREMENT":
                reg_bin = instruction_code[4:7]
                reg = registers_reverse.get(reg_bin, "UNKNOWN")
                asm_instruction += f" {reg}"
            elif instruction_name == "YELLSTR":
                string_index_bin = instruction_code[7:]
                try:
                    string_index = int(string_index_bin, 2)
                    string_label = f"STRING_LITERAL_{string_index}"
                    asm_instruction += f" {string_label}"
                    if string_label not in string_literals_discovered:
                        string_literals_discovered[string_label] = f"\"UNKNOWN_STRING_{string_index}\\n\"" # Placeholder
                except ValueError:
                    asm_instruction += " UNKNOWN_STRING"
            elif instruction_name == "YELLVAL":
                reg_bin = instruction_code[4:7]
                reg = registers_reverse.get(reg_bin, "UNKNOWN")
                asm_instruction += f" {reg}"
            elif instruction_name == "HALT":
                pass # No operands
            elif instruction_name == "NOTGREATEROREQUAL":
                reg1_bin = instruction_code[4:7]
                reg2_bin = instruction_code[7:10]
                label_address_bin = instruction_code[10:]
                reg1 = registers_reverse.get(reg1_bin, "UNKNOWN")
                reg2 = registers_reverse.get(reg2_bin, "UNKNOWN")
                try:
                    label_target_address = int(label_address_bin, 2) * 2
                    label = address_to_label.get(label_target_address, f"LABEL_TARGET_{label_target_address // 2}")
                    asm_instruction += f" {reg1}, {reg2}, {label}"
                except ValueError:
                    asm_instruction += f" {reg1}, {reg2}, UNKNOWN_LABEL"

            assembly_lines.append(asm_instruction)
        else:
            assembly_lines.append(f".UNKNOWN_INSTRUCTION {instruction_code}")

        current_address += 2

    # Add string literals at the beginning of the disassembled file
    string_definitions = [f"{label}: .STRING {literal}" for label, literal in string_literals_discovered.items()]
    full_assembly = string_definitions + [""] + assembly_lines

    try:
        with open(outfile_path, "w") as outfile:
            outfile.write("\n".join(full_assembly) + "\n")
        print(f"Disassembled '{mc_file}' -> '{outfile_path}'")
    except Exception as e:
        print(f"Error writing to output file '{outfile_path}': {e}")

if __name__ == "__main__":
    mc_files = ["addition.mc", "conditional.mc", "fizzbuzz.mc"]
    for mc_file in mc_files:
        asm_file = mc_file.replace(".mc", "_disassembled.asm")
        disassemble(mc_file, asm_file)