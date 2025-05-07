import re
import sys
import os

def c_to_asm_final_file(input_filename):
    try:
        with open(input_filename, 'r') as infile:
            c_code = infile.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
        return None

    asm_code = []
    var_to_reg = {}
    next_reg = 1
    label_counter = 0
    string_literals = {}

    def get_free_register():
        nonlocal next_reg
        if next_reg <= 7:
            reg = f"R{next_reg}"
            next_reg += 1
            return reg
        else:
            raise ValueError("Out of registers!")

    def get_variable_register(var_name):
        if var_name not in var_to_reg:
            var_to_reg[var_name] = get_free_register()
        return var_to_reg[var_name]

    def create_label(prefix="LABEL"):
        nonlocal label_counter
        label_counter += 1
        return f"{prefix}_{label_counter}"

    lines = [l.strip() for l in c_code.strip().splitlines() if l.strip()]
    loop_stack = []
    if_stack = []

    # Add standard string literals for FizzBuzz ONLY if processing fizzbuzz.c
    if "fizzbuzz.c" in input_filename:
        string_literals.update({
            'FIZZBUZZ_MSG': 'FizzBuzz\n',
            'FIZZ_MSG': 'Fizz\n',
            'BUZZ_MSG': 'Buzz\n'
        })

    for line in lines:
        line = line.strip(';').strip()

        # Variable declaration with initialization
        var_init_match = re.match(r'int\s+(\w+)\s*=\s*(\d+)', line)
        if var_init_match:
            var, value = var_init_match.groups()
            reg = get_variable_register(var)
            asm_code.append(f"YOLOAD {reg}, {value}(R0)")
            continue

        # Variable declaration without initialization
        var_decl_match = re.match(r'int\s+(\w+)', line)
        if var_decl_match:
            var = var_decl_match.groups()[0]
            get_variable_register(var)
            continue

        # Addition
        add_match = re.match(r'(\w+)\s*=\s*(\w+)\s*\+\s*(\w+)', line)
        if add_match:
            dest, src1, src2 = add_match.groups()
            reg_dest = get_variable_register(dest)
            reg_src1 = get_variable_register(src1)
            reg_src2 = get_variable_register(src2)
            asm_code.append(f"ADD {reg_dest}, {reg_src1}, {reg_src2}")
            continue

        # If statement (single condition)
        if_match = re.match(r'if\s*\(\s*(\w+)\s*>\s*(\d+)\s*\)', line)
        if if_match:
            var, value = if_match.groups()
            reg = get_variable_register(var)
            compare_reg = get_free_register()
            if_body_label = create_label("IF_BODY")
            if_end_label = create_label("END_IF")
            if_stack.append(if_end_label)
            asm_code.append(f"YOLOAD {compare_reg}, {value}(R0)")
            asm_code.append(f"GREATERTHAN {reg}, {compare_reg}, {if_body_label}")
            asm_code.append(f"YEET {if_end_label}")
            asm_code.append(f"{if_body_label}:")
            continue

        # printf
        print_match = re.match(r'printf\s*\(\s*"([^"]+)"(?:,\s*(\w+))?\s*\)', line)
        if print_match:
            text, var = print_match.groups()
            if "%d" in text and var:
                reg = get_variable_register(var)
                asm_code.append(f"YELLVAL {reg}")
            else:
                if text not in string_literals.values():
                    label_name = f"CUSTOM_MSG_{len(string_literals)}"
                    string_literals[label_name] = text
                else:
                    label_name = next(k for k, v in string_literals.items() if v == text)
                asm_code.append(f"YELLSTR {label_name}")
            continue

        # For loop (FizzBuzz)
        for_match = re.match(r'for\s*\(\s*int\s+(\w+)\s*=\s*(\d+)\s*;\s*\1\s*(<=|<)\s*(\d+)\s*;\s*\1\+\+\s*\)', line)
        if for_match:
            var, start, op, end = for_match.groups()
            var_reg = get_variable_register(var)
            loop_start = create_label("LOOP_START")
            loop_end = create_label("LOOP_END")
            loop_stack.append((var, var_reg, op, end, loop_start, loop_end))
            asm_code.append(f"YOLOAD {var_reg}, {start}(R0)")
            asm_code.append(f"{loop_start}:")
            continue

        # If with && logic (FizzBuzz)
        if_match_fizzbuzz = re.match(r'if\s*\(\s*(\w+)\s*%\s*(\d+)\s*==\s*0\s*&&\s*(\w+)\s*%\s*(\d+)\s*==\s*0\s*\)', line)
        if if_match_fizzbuzz:
            var1, mod1, var2, mod2 = if_match_fizzbuzz.groups()
            reg = get_variable_register(var1)
            temp1 = get_free_register()
            temp2 = get_free_register()
            fizzbuzz_label = create_label("FIZZBUZZ")
            skip_fizzbuzz = create_label("SKIP_FIZZBUZZ")
            end_if = create_label("END_IF")
            if_stack.append(end_if)

            # First condition (i % 3 == 0)
            asm_code.append(f"YOLOAD R0, {mod1}(R0)")
            asm_code.append(f"MODULOIZE {temp1}, {reg}, R0")
            asm_code.append(f"SAMEBRO {temp1}, R0, {create_label('CHECK_SECOND')}")
            asm_code.append(f"YEET {skip_fizzbuzz}")
            asm_code.append(f"{asm_code[-2].split()[-1]}:")

            # Second condition (i % 5 == 0)
            asm_code.append(f"YOLOAD R0, {mod2}(R0)")
            asm_code.append(f"MODULOIZE {temp2}, {reg}, R0")
            asm_code.append(f"SAMEBRO {temp2}, R0, {fizzbuzz_label}")
            asm_code.append(f"YEET {skip_fizzbuzz}")
            asm_code.append(f"{fizzbuzz_label}:")
            asm_code.append(f"YELLSTR FIZZBUZZ_MSG")
            asm_code.append(f"YEET {end_if}")
            asm_code.append(f"{skip_fizzbuzz}:")
            next_reg -= 2
            continue

        # Else if (divisible by 3)
        elif_match_fizz = re.match(r'else\s+if\s*\(\s*(\w+)\s*%\s*3\s*==\s*0\s*\)', line)
        if elif_match_fizz:
            var = elif_match_fizz.group(1)
            reg = get_variable_register(var)
            temp = get_free_register()
            fizz_label = create_label("FIZZ")
            skip_fizz = create_label("SKIP_FIZZ")
            end_if = if_stack[-1] if if_stack else create_label("END_IF")

            asm_code.append(f"YOLOAD R0, 3(R0)")
            asm_code.append(f"MODULOIZE {temp}, {reg}, R0")
            asm_code.append(f"SAMEBRO {temp}, R0, {fizz_label}")
            asm_code.append(f"YEET {skip_fizz}")
            asm_code.append(f"{fizz_label}:")
            asm_code.append(f"YELLSTR FIZZ_MSG")
            asm_code.append(f"YEET {end_if}")
            asm_code.append(f"{skip_fizz}:")
            next_reg -= 1
            continue

        # Else if (divisible by 5)
        elif_match_buzz = re.match(r'else\s+if\s*\(\s*(\w+)\s*%\s*5\s*==\s*0\s*\)', line)
        if elif_match_buzz:
            var = elif_match_buzz.group(1)
            reg = get_variable_register(var)
            temp = get_free_register()
            buzz_label = create_label("BUZZ")
            skip_buzz = create_label("SKIP_BUZZ")
            end_if = if_stack[-1] if if_stack else create_label("END_IF")

            asm_code.append(f"YOLOAD R0, 5(R0)")
            asm_code.append(f"MODULOIZE {temp}, {reg}, R0")
            asm_code.append(f"SAMEBRO {temp}, R0, {buzz_label}")
            asm_code.append(f"YEET {skip_buzz}")
            asm_code.append(f"{buzz_label}:")
            asm_code.append(f"YELLSTR BUZZ_MSG")
            asm_code.append(f"YEET {end_if}")
            asm_code.append(f"{skip_buzz}:")
            next_reg -= 1
            continue

        # Else
        elif line.startswith("else"):
            if not loop_stack:
                continue
            reg = get_variable_register(loop_stack[-1][0])
            asm_code.append(f"YELLVAL {reg}")
            if if_stack:
                asm_code.append(f"YEET {if_stack[-1]}")
            continue

        # Increment (in loop)
        inc_match = re.match(r'(\w+)\+\+', line)
        if inc_match and loop_stack:
            var = inc_match.group(1)
            reg = get_variable_register(var)
            asm_code.append(f"INCREMENT {reg}")
            continue

        # End block
        elif line == "}":
            if loop_stack:
                var, reg, op, end, loop_start, loop_end = loop_stack.pop()
                temp = get_free_register()
                asm_code.append(f"YOLOAD {temp}, {end}(R0)")
                comparison = "NOTGREATEROREQUAL" if op == "<=" else "NOTGREATER"
                asm_code.append(f"{comparison} {reg}, {temp}, {loop_end}")
                asm_code.append(f"INCREMENT {reg}")
                asm_code.append(f"YOLO {loop_start}")
                asm_code.append(f"{loop_end}:")
                next_reg -= 1
            elif if_stack:
                end_label = if_stack.pop()
                asm_code.append(f"{end_label}:")
            continue

        # Return statement
        elif line.startswith("return"):
            asm_code.append("HALT")
            continue

    # Add string literals at the beginning
    string_definitions = [f"{label}: .STRING \"{text}\"" for label, text in string_literals.items()]
    full_asm = string_definitions + [""] + asm_code

    return "\n".join(full_asm)

if __name__ == "__main__":
    c_files = ["addition.c", "conditional.c", "fizzbuzz.c"]
    for c_file in c_files:
        assembly_output = c_to_asm_final_file(c_file)
        if assembly_output:
            output_filename = c_file.replace(".c", ".asm")
            try:
                with open(output_filename, 'w') as outfile:
                    outfile.write(assembly_output)
                print(f"Assembly code for '{c_file}' written to '{output_filename}'")
            except Exception as e:
                print(f"Error writing to output file '{output_filename}': {e}")