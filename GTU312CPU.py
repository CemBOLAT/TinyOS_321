class GTU312CPU:
    MEMORY_SIZE_DATA = 2 ** 16  # 65K memory
    MEMORY_SIZE_OS = 21
    PC = 0
    SP = 1
    SYSCALL_RESULT = 2
    INSTR_COUNT = 3

    START_OF_USER_MODE_ADDR = 1000

    def __init__(self, debug_level=1):
        self.memory = [0] * self.MEMORY_SIZE_DATA
        #self.memory = [0] * self.MEMORY_SIZE_OS
        self.debug_level = debug_level
        self.mode = "kernel"  # kernel or user
        self.running = True

    def load_from_file(self, filepath):
        is_data = False
        is_instr = False

        try:
            with open(filepath, 'r') as file:
                for line in file:
                    # Yorumu at (varsa)
                    line = line.split('#')[0].strip()

                    if not line:
                        continue  # boş satır

                    # Bölüm giriş/çıkış kontrolleri
                    if "Begin Data Section" in line:
                        is_data = True
                        continue
                    elif "End Data Section" in line:
                        is_data = False
                        continue
                    elif "Begin Instruction Section" in line:
                        is_instr = True
                        continue
                    elif "End Instruction Section" in line:
                        is_instr = False
                        continue

                    # Veri satırı: "adres değer"
                    if is_data:
                        tokens = line.split()
                        if len(tokens) >= 2:
                            addr = int(tokens[0])
                            value = int(tokens[1])
                            self.memory[addr] = value
                        else:
                            print(f"[!] Geçersiz veri satırı: {line}")

                    # Komut satırı: "adres KOMUT ARG1 ARG2 ..."
                    elif is_instr:
                        tokens = line.split()
                        if len(tokens) >= 2:
                            addr = int(tokens[0])
                            instr = ' '.join(tokens[1:])
                            self.memory[addr] = instr
                        else:
                            print(f"[!] Geçersiz komut satırı: {line}")

            print(f"[✓] .gtu312 dosyası başarıyla yüklendi: {filepath}")

        except FileNotFoundError:
            print(f"[!] Dosya bulunamadı: {filepath}")

    def execute(self):
        
        while self.running and self.memory[self.PC] < self.MEMORY_SIZE_DATA :
            pc = self.memory[self.PC]
            instr = self.memory[pc]

            print(f"[PC={pc}] Executing: {instr}")

            if not isinstance(instr, str):
                break

            tokens = instr.strip().split()
            op = tokens[0]

            try:
                if op == "SET":
                    # SET B A: Set the A-th memory location to number B.
                    # Example: SET -20, 100 writes the value of -20 to memory location 100.
                    B, A = int(tokens[1]), int(tokens[2])
                    if not self.is_valid_address(A):
                        print(f"[!] Invalid address: {A}")
                        self.running = False
                    self.memory[A] = B

                elif op == "CPY":
                    # CPY A1 A2 : Direct Copy: Copy the content of memory location A1 to memory A2.
                    # Example: CPY 100, 120 copies the memory value of address 100 to the memory address 120
                    A1, A2 = int(tokens[1]), int(tokens[2])
                    if not self.is_valid_address(A1) or not self.is_valid_address(A2):
                        print(f"[!] Invalid address: {A1} or {A2}")
                        self.running = False
                    self.memory[A2] = self.memory[A1]

                elif op == "CPYI":
                    # CPYI A1 A2 : Indirect Copy: Copy the content of memory location A1 to memory A2.
                    # Example: CPYI 100, 102: if memory address 100 contains 200, then this instruction copies the contents of memory address 200 to memory location 120.
                    A1, A2 = int(tokens[1]), int(tokens[2])
                    if not self.is_valid_address(A1) or not self.is_valid_address(A2):
                        print(f"[!] Invalid address: {A1} or {A2}")
                        self.running = False
                    self.memory[A2] = self.memory[self.memory[A1]]

                elif op == "ADD":
                    # ADD A B: Add number B to memory[A]
                    A, B = int(tokens[1]), int(tokens[2])
                    if not self.is_valid_address(A):
                        print(f"[!] Invalid address: {A}")
                        self.running = False
                    self.memory[A] += B

                elif op == "ADDI":
                    # ADDI A1 A2: memory[A1] += memory[A2]
                    a1, a2 = int(tokens[1]), int(tokens[2])
                    if not self.is_valid_address(a1) or not self.is_valid_address(a2):
                        print(f"[!] Invalid address: {a1} or {a2}")
                        self.running = False
                    self.memory[a1] += self.memory[a2]

                elif op == "SUBI":
                    # SUBI A1 A2:  Subtract the contents of memory address A2 from address A1, put the result in A2
                    a1, a2 = int(tokens[1]), int(tokens[2])
                    if not self.is_valid_address(a1) or not self.is_valid_address(a2):
                        print(f"[!] Invalid address: {a1} or {a2}")
                        self.running = False
                    self.memory[a2] = self.memory[a1] - self.memory[a2] # hmm
                elif op == "JIF":
                    # JIF A C: if memory[A] <= 0 then PC = C
                    cond, target = int(tokens[1]), int(tokens[2])
                    if not self.is_valid_address(cond) or not self.is_valid_address(target):
                        print(f"[!] Invalid address: {cond} or {target}")
                        self.running = False
                    if self.memory[cond] <= 0: # kkk
                        self.memory[self.PC] = target
                        continue

                elif op == "PUSH":
                    # PUSH A: Push memory[A] to the stack
                    # Stack grows downwards.
                    addr = int(tokens[1])
                    if not self.is_valid_address(addr):
                        print(f"[!] Invalid address: {addr}")
                        self.running = False
                    sp = self.memory[self.memory[self.SP]]
                    self.memory[sp] = self.memory[addr]
                    self.memory[self.memory[self.SP]] -= 1

                elif op == "POP":
                    # POP A: Pop value from stack to memory[A]
                    self.memory[self.memory[self.SP]] += 1
                    sp = self.memory[self.memory[self.SP]]
                    dst = int(tokens[1])
                    self.memory[dst] = self.memory[sp]

                elif op == "CALL":
                    # CALL C: Call subroutine at instruction C, push return address.
                    C = int(tokens[1])
                    if not self.is_valid_address(C):
                        print(f"[!] Invalid address: {C}")
                        self.running = False
                    ret_addr = self.memory[self.PC] + 1
                    sp = self.memory[self.memory[self.SP]]
                    self.memory[sp] = ret_addr
                    self.memory[self.SP] -= 1
                    self.memory[self.PC] = C
                    continue

                elif op == "RET":
                    # RET: Pop return address from stack and jump there
                    self.memory[self.SP] += 1
                    sp = self.memory[self.memory[self.SP]]
                    self.memory[self.PC] = self.memory[sp]
                    continue

                elif op == "USER":
                    # USER: Switch to user mode (placeholder)
                    self.mode = "user"

                elif op == "SYSCALL":
                    #("[SYSCALL] System call requested.")
                    syscall = tokens[1]
                    if syscall == "PRN":
                        # SYSCALL PRN A: Print memory[A]
                        addr = int(tokens[2])
                        print(f"[SYSCALL PRN] {self.memory[addr]}")
                        self.memory[self.SYSCALL_RESULT] = self.memory[addr]
                        # Not: Blocking 100 instructions to simulate delay handled externally
                        # how to handle blocking? 
                    elif syscall == "HLT":
                        # SYSCALL HLT: Shuts down the thread
                        print("[SYSCALL HLT] Halting CPU.")
                        self.running = False
                    elif syscall == "YIELD":
                        # SYSCALL YIELD: Yield CPU to OS
                        print("[SYSCALL YIELD] Yield requested.")
                    else:
                        print(f"[!] Unknown SYSCALL: {syscall}")

                elif op == "HLT":
                    # HLT: Hard halt
                    print("[HLT] CPU halted.")
                    self.running = False

                else:
                    print(f"[!] Unknown instruction: {op}")
                    break

            except Exception as e:
                print(f"[!] Error: {e} at PC={self.memory[self.PC]} → {instr}")
                break

            self.memory[self.PC] += 1
            self.memory[self.INSTR_COUNT] += 1

            if self.debug_level == 1:
                self.print_memory()
            elif self.debug_level == 2:
                self.print_memory()
                input("Enter to continue...")

        print("[✓] is_running: ", self.memory[self.PC])

    def print_memory(self, limit=20):
        print("Memory [0-{}]:".format(limit - 1), self.memory[:limit])
        #print("Memory [50-{}]:".format(limit - 1), self.memory[50:limit])

    def is_valid_address(self, addr):
        # if it is negative return false.
        # if it is positive but less than 1000 in user mode, return false.
        # if it is greater than 65535, return false.
        # if addr < 0 or addr >= self.MEMORY_SIZE_DATA :
        #     return False
        # if addr < self.START_OF_USER_MODE_ADDR and self.mode == "user":
        #     return False
        return True

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="GTU-312 CPU Simulator")
    parser.add_argument("filename", help="Input .gtu312 program file")
    parser.add_argument("-D", type=int, default=0, choices=[0, 1, 2], help="Debug mode: 0, 1 or 2")
    args = parser.parse_args()

    cpu = GTU312CPU(debug_level=args.D)
    cpu.load_from_file(args.filename)
    cpu.execute()