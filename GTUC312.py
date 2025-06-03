import sys

class GTUC312:

    dataMemorySize = 2 ** 14  # 16K memory
    instructionMemorySize = 2 ** 14  # 16K memory

    systemCallPrintLocation = 430
    systemCallHaltLocation = 450
    systemCallYieldLocation = 466
    cpuHaltLocation = 429

    PC_Location = 0  # Program Counter location in data memory
    SP_Location = 1  # Stack Pointer location in data memory
    IC_Location = 2  # Instruction Counter location in data memory

    def __init__(self, debugMode: int = 0):
        self.dataMemory = [0] * self.dataMemorySize # Initialize data memory with zeros
        self.instructionMemory = ["" for _ in range(self.instructionMemorySize)]
        self.ishalted = False
        self.isKernelMode = False
        self.debugMode = debugMode

        if debugMode < 0 or debugMode > 3:
            self.ishalted = True
            print("Invalid debug mode. CPU halted. (0: After CPU halts, 1: After each instruction, 2: After each instruction with keypress, 3: After each context switch or system call)")
        

        self.dataMemory[0] = 0 # PC 0
        self.dataMemory[1] = self.dataMemorySize - 1 # SP 1 


    def setHalted(self, value: bool):
        """Set the halted state of the CPU."""
        self.ishalted = value

    def isHalted(self) -> bool:
        """Check if the CPU is halted."""
        return self.ishalted
    
    def setKernelMode(self, value: bool):
        """Set the kernel mode state of the CPU."""
        self.isKernelMode = value

    def isKernelMode(self) -> bool:
        """Check if the CPU is in kernel mode."""
        return self.isKernelMode

    def getDataMemory(self, address: int) -> int:
        """Get the value from data memory at the specified address."""
        if 0 <= address < self.dataMemorySize:
            return self.dataMemory[address]
        else:
            raise IndexError("Data memory address out of bounds " + str(address))
        
    def setDataMemory(self, address: int, value: int):
        """Set the value in data memory at the specified address."""
        if 0 <= address < self.dataMemorySize:
            self.dataMemory[address] = value
        else:
            raise IndexError("Data memory address out of bounds " + str(address))
        
    def getInstructionMemory(self, address: int) -> str:
        """Get the instruction from instruction memory at the specified address."""
        if 0 <= address < self.instructionMemorySize:
            return self.instructionMemory[address]
        else:
            raise IndexError("Instruction memory address out of bounds " + str(address))
        
    def setInstructionMemory(self, address: int, instruction: str):
        """Set the instruction in instruction memory at the specified address."""
        if 0 <= address < self.instructionMemorySize:
            self.instructionMemory[address] = instruction
        else:
            raise IndexError("Instruction memory address out of bounds " + str(address))
        

    def load_program(self, filename: str):
        """Load a program from a file into instruction memory."""
        try:
            with open(filename, 'r') as file:
                instructions = file.readlines()
                inDataSection = False
                inInstructionSection = False
                for i, instruction in enumerate(instructions):
                    instruction = instruction.strip() # Remove leading/trailing whitespace
                    if not instruction:
                        continue
                    comment_sign_position = instruction.find('#')
                    if comment_sign_position != -1: # Remove comments
                        instruction = instruction[:comment_sign_position].strip()
                    else: # No comment, just strip whitespace
                        instruction = instruction.strip()

                    if not instruction:  # Skip empty lines
                        continue

                    if instruction.find('Begin Data Section') != -1:
                        inDataSection = True
                        inInstructionSection = False
                        continue
                    elif instruction.find('End Data Section') != -1:
                        inDataSection = False
                        inInstructionSection = True
                        continue
                    elif instruction.find('Begin Instruction Section') != -1:
                        inInstructionSection = True
                        inDataSection = False
                        continue
                    elif instruction.find('End Instruction Section') != -1:
                        inInstructionSection = False
                        continue

                    if inDataSection:
                        # Split on whitespace
                        parts = instruction.split()
                        if len(parts) >= 2:  # Make sure we have at least 2 parts
                            addr = int(parts[0])
                            value = int(parts[1])
                            self.setDataMemory(addr, value)
                    elif inInstructionSection:
                        # Split on whitespace, but only for the first occurrence
                        parts = instruction.split(maxsplit=1)
                        if len(parts) >= 2:  # Make sure we have at least 2 parts
                            addr = int(parts[0])
                            instr = parts[1].strip()
                            self.setInstructionMemory(addr, instr)

                print(f"Program loaded from {filename}")

        except FileNotFoundError:
            raise FileNotFoundError(f"File {filename} not found")
        except Exception as e:
            raise e
        
    def memoryAccessCheck(self, address: int):
        if address < 0 or address >= self.dataMemorySize:
            # Executre system call halt
            print("Memory access out of bounds: " + str(address))
            self.dataMemory[2] = -1 # store system call status
            print("Thread ID: " + str(self.getDataMemory(self.currentThreadIDRegisterLocation)))
            self.systemCallExecution(syscall="HLT", param=0)

    def systemCallExecution(self, syscall: str, param: int):
        self.setKernelMode(True)


        id = self.getDataMemory(21) # Get current thread ID

        addr = (40 * id) + 50 + 4

        self.setDataMemory(addr, self.getDataMemory(0) + 1) # Increment PC

        if syscall == "PRN":
            print("PRN: " + str(self.getDataMemory(param)))
            self.dataMemory[0] = self.systemCallPrintLocation
        elif syscall == "HLT":
            self.dataMemory[0] = self.systemCallHaltLocation
        elif syscall == "YIELD":
            self.dataMemory[0] = self.systemCallYieldLocation
        else:
            self.dataMemory[0] = self.cpuHaltLocation
            raise ValueError("Unknown system call: " + syscall)
    
    def execute(self):
        """Execute the next instruction in instruction memory."""
        if self.isHalted():
            print("CPU is halted. Cannot execute instructions.")
            return
        
        pc = self.getDataMemory(self.PC_Location)
        instruction = self.getInstructionMemory(pc)

        if not instruction:
            self.setDataMemory(self.PC_Location, pc + 1)  # Increment PC if no instruction found
            return
        
        self.setDataMemory(self.IC_Location, self.getDataMemory(self.IC_Location) + 1)

        parts = instruction.split()
        
        opcode = parts[0]
        args = parts[1:]

        is_switch_required = False
        
        if (opcode == "HLT" and len(parts) == 1):
            self.setHalted(True)
            print("Halting CPU.")
            return
        elif (opcode == "SYSCALL" and len(parts) == 2):
            syscall_type = parts[1]
            is_switch_required = True
            self.systemCallExecution(syscall=syscall_type, param=0)
        elif (opcode == "SYSCALL" and len(parts) == 3):
            syscall_type = parts[1]
            param = int(parts[2])
            is_switch_required = True
            self.systemCallExecution(syscall=syscall_type, param=param)
        elif opcode == "SET":
            
            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 2:
                raise ValueError("Invalid SET instruction format. Expected: SET <address> <value>")
            value= int(args[0])
            address = int(args[1])
            self.memoryAccessCheck(address)
            self.setDataMemory(address, value)
        elif opcode == "CPY":

            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 2:
                raise ValueError("Invalid CPY instruction format. Expected: CPY <source_address> <destination_address>")
            source_address = int(args[0])
            destination_address = int(args[1])
            self.memoryAccessCheck(source_address)
            self.memoryAccessCheck(destination_address)
            self.setDataMemory(destination_address, self.getDataMemory(source_address))

        elif opcode == "CPYI":
            
            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 2:
                raise ValueError("Invalid COPYI instruction format. Expected: COPYI <source_address> <destination_address>")
            source_address = int(args[0])
            destination_address = int(args[1])
            self.memoryAccessCheck(source_address) # check source address
            self.memoryAccessCheck(self.getDataMemory(source_address)) # check value at source address
            self.memoryAccessCheck(destination_address) # check destination address
            self.setDataMemory(destination_address, self.getDataMemory(self.getDataMemory(source_address)))

        elif opcode == "CPYI2":
            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 2:
                raise ValueError("Invalid CPYI2 instruction format. Expected: CPYI2 <source_address> <destination_address>")
            
            source_address = int(args[0])
            destination_address = int(args[1])

            self.memoryAccessCheck(source_address)
            self.memoryAccessCheck(destination_address)

            indirect_source_address = self.getDataMemory(source_address)
            indirect_destination_address = self.getDataMemory(destination_address)

            self.memoryAccessCheck(indirect_source_address)
            self.memoryAccessCheck(indirect_destination_address)

            self.setDataMemory(indirect_destination_address, self.getDataMemory(indirect_source_address))
        elif opcode == "ADD":
            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 2:
                raise ValueError("Invalid ADD instruction format. Expected: ADD <address1> <address2>")
            
            address = int(args[0])
            value = int(args[1])

            self.memoryAccessCheck(address)
            self.setDataMemory(address, self.getDataMemory(address) + value)

        elif opcode == "ADDI":
            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 2:
                raise ValueError("Invalid ADDI instruction format. Expected: ADDI <address> <value>")
            
            address1 = int(args[0])
            address2 = int(args[1])

            self.memoryAccessCheck(address1)
            self.memoryAccessCheck(address2)

            self.setDataMemory(address1, self.getDataMemory(address1) + self.getDataMemory(address2))

        elif opcode == "SUBI":
            
            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 2:
                raise ValueError("Invalid SUBI instruction format. Expected: SUBI <address> <value>")
            
            address1 = int(args[0])
            address2 = int(args[1])

            self.memoryAccessCheck(address1)
            self.memoryAccessCheck(address2)

            self.setDataMemory(address2, self.getDataMemory(address1) - self.getDataMemory(address2))

        elif opcode == "JIF":

            if len(args) != 2:
                raise ValueError("Invalid JIF instruction format. Expected: JIF <address> <value>")            
            address = int(args[0])
            value = int(args[1])

            self.memoryAccessCheck(address)
            if (self.getDataMemory(address) <= 0):
                # set PC to value
                self.setDataMemory(self.PC_Location, value)
            else:
                self.setDataMemory(self.PC_Location, pc + 1)
        
        elif opcode == "PUSH":
            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 1:
                raise ValueError("Invalid PUSH instruction format. Expected: PUSH <address>")
            address = int(args[0])

            self.memoryAccessCheck(address)

            sp = self.getDataMemory(self.SP_Location)

            new_sp = sp - 1
            self.memoryAccessCheck(new_sp)
                
            self.setDataMemory(self.SP_Location, new_sp)

            self.setDataMemory(self.getDataMemory(self.SP_Location), self.getDataMemory(address))

        elif opcode == "POP":
            self.setDataMemory(self.PC_Location, pc + 1)

            if len(args) != 1:
                raise ValueError("Invalid POP instruction format. Expected: POP <address>")
            address = int(args[0])

            self.memoryAccessCheck(address)

            sp = self.getDataMemory(self.SP_Location)

            self.memoryAccessCheck(sp)

            value = self.getDataMemory(sp)
            self.setDataMemory(address, value)

            new_sp = sp + 1
            self.memoryAccessCheck(new_sp)
                
            self.setDataMemory(self.SP_Location, new_sp)

        elif opcode == "CALL":
            if len(args) != 1:
                raise ValueError("Invalid CALL instruction format. Expected: CALL <address>")
            
            address = int(args[0])

            sp = self.getDataMemory(self.SP_Location)
            pc = self.getDataMemory(self.PC_Location)

            self.setDataMemory(self.SP_Location, sp - 1)  # Decrement SP for return address
            self.memoryAccessCheck(self.getDataMemory(self.SP_Location))
            self.setDataMemory(self.getDataMemory(self.SP_Location), pc + 1)
            self.memoryAccessCheck(address)
            self.setDataMemory(self.PC_Location, address)

        elif opcode == "RET" and len(args) == 0:
            self.memoryAccessCheck(self.getDataMemory(self.SP_Location))
            self.setDataMemory(self.PC_Location, self.getDataMemory(self.getDataMemory(self.SP_Location)))
            self.setDataMemory(self.SP_Location, self.getDataMemory(self.SP_Location) + 1)

        elif opcode == "USER":

            id = self.getDataMemory(21)  # Get current thread ID
            addr = (40 * id) + 50 + 4
            self.memoryAccessCheck(addr)

            self.setDataMemory(self.PC_Location, self.getDataMemory(addr))  # Set PC to thread's PC
            self.setKernelMode(False)  # Switch to user mod
            is_switch_required = True


        if self.debugMode == 1:
            self.printMemory()
        elif self.debugMode == 2:
            self.printMemory()
            input("Press Enter to continue...")
        if self.debugMode == 3 and is_switch_required:
            self.printThreadTable()

    def printThreadTable(self, id: int = -1):

        
        offset_and_strings = {
            0: "Thread ID",
            1: "Start Time",
            2: "Execution Time",
            3: "Thread State", # 0: "Ready", 1: "Running", 2: "Blocked"
            4: "PC",
            5: "SP",
        }

        id = self.getDataMemory(21)

        base_location = (40 * id) + 50

        print("=== THREAD TABLE ===")

        for i in range(len(offset_and_strings)):
            if id == -1:
                print(f"{offset_and_strings[i]}: {self.getDataMemory(base_location + i)}")
            else:
                print(f"{offset_and_strings[i]}: {self.getDataMemory(base_location + i)} (Thread ID: {id})")

        print("Saved Registers:")

        for i in range(1, 21): # 2 < 21
            addr2 = base_location + 10 + i
            print(f"  Register[{i}] = {self.getDataMemory(addr2)}")


        print("====================")

    def printMemory(self):
        print("=== MEMORY STATE ===")
        print("PC:", self.getDataMemory(self.PC_Location), "SP:", self.getDataMemory(self.SP_Location), "Executed:", self.getDataMemory(self.IC_Location))

        print("Memory in 22. register:", self.getDataMemory(22))

        print("Whole Data Memory without zeros:")
        for i in range(self.dataMemorySize):
            if self.dataMemory[i] != 0:
                print(f"  Data[{i}] = {self.dataMemory[i]}")

        print("Whole Instruction Memory without empty strings:")
        for i in range(self.instructionMemorySize):
            if self.instructionMemory[i] != "":
                print(f"  Instr[{i}] = {self.instructionMemory[i]}")
        print("=== END OF MEMORY STATE ===")
        

if __name__ == "__main__":


    try:
        # python3 GTUC312.py filename -D 0|1|2|3
        debugMode = 0
        if len(sys.argv) > 1:
            filename = sys.argv[1]
            if len(sys.argv) == 4 and sys.argv[2] == "-D":
                debugMode = int(sys.argv[3])
            else:
                raise ValueError("Invalid arguments. Usage: python3 GTUC312.py <filename> [-D <debugMode>]")
        else:
            raise ValueError("No filename provided. Usage: python3 GTUC312.py <filename> [-D <debugMode>]")


        cpu = GTUC312(debugMode=debugMode)
        print("GTU-C312 CPU initialized.")
        
        
        cpu.load_program(filename)

        while not cpu.isHalted():
            cpu.execute()

        if debugMode == 0:
            print("Final Thread Table:")
            cpu.printMemory()
    except Exception as e:
        print(e)