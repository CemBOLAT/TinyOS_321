#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>

class CPU {
private:
    std::vector<long> dataMemory;         // Data memory array (integers only)
    std::vector<std::string> instructionMemory;  // Instruction memory (strings)
    bool halted;                          // CPU halt flag
    bool kernelMode;                      // CPU mode (kernel or user)
    int debugMode;                        // Debug mode flag (0-3)
    
    // Helper function to check user mode memory access
    void checkMemoryAccess(long address) {
        if ((!kernelMode && address < 1000) || address >= 11000) {
            std::cerr << "MEMORY ACCESS VIOLATION: User mode tried to access address " << address << std::endl;
            dataMemory[2] = -1;  // Store error in syscall result
            // Terminate the current thread
            std::cerr << "Thread " << dataMemory[21]  << " terminated due to memory violation" << std::endl;
            executeSystemCall("HLT", 0);
        }
    }

    // System call handler
    void executeSystemCall(const std::string& syscallType, long arg) {
        kernelMode = true;
        
        dataMemory[50 + 40*dataMemory[21] + 4] = dataMemory[0] + 1; 

        if (syscallType == "PRN") {
            std::cout << "OUTPUT: " << dataMemory[arg] << std::endl;
            dataMemory[0] = 430;
        }
        else if (syscallType == "HLT") {
            dataMemory[0] = 450;
        }
        else if (syscallType == "YIELD") {
            dataMemory[0] = 466;
        }
        else {
            std::cerr << "Unknown system call: " << syscallType << std::endl;
            dataMemory[0] = 429;  // Halt the cpu.
        }
        
    }
    
    // Parse instruction string and extract components
    void parseInstruction(const std::string& instruction, std::string& cmd, std::vector<long>& args) {
        std::istringstream iss(instruction);
        std::string token;
        
        args.clear();
        
        // Get command
        if (iss >> cmd) {
            // Get arguments
            while (iss >> token) {
                try {
                    args.push_back(std::stol(token));
                } catch (const std::exception& e) {
                    // If conversion fails, it might be a string argument (for SYSCALL)
                    // Handle this case separately in execute()
                }
            }
        }
    }

public:
    // Constructor
    CPU(size_t dataMemorySize = 11000, size_t instructionMemorySize = 11000) :
        dataMemory(dataMemorySize, 0),
        instructionMemory(instructionMemorySize, ""),
        halted(false), 
        kernelMode(true),
        debugMode(0) { // Start in kernel mode
        
        // Initialize registers
        dataMemory[0] = 0;  // PC = 0
        dataMemory[1] =   - 1;  // SP at the end of memory
    }
    

    // Add this setter method to CPU class:
    void setDebugMode(int mode) {
        debugMode = mode;
    }


    // Check if CPU is halted
    bool isHalted() const {
        return halted;
    }
    
    // Set data memory location
    void setDataMemory(long address, long value) {
        if (address >= 0 && address < static_cast<long>(dataMemory.size())) {
            dataMemory[address] = value;
        } else {
            std::cerr << "Data memory access out of bounds: " << address << std::endl;
        }
    }
    
    // Get data memory value
    long getDataMemory(long address) const {
        if (address >= 0 && address < static_cast<long>(dataMemory.size())) {
            return dataMemory[address];
        } else {
            std::cerr << "Data memory access out of bounds: " << address << std::endl;
            return 0;
        }
    }
    
    // Set instruction memory location
    void setInstructionMemory(long address, const std::string& instruction) {
        if (address >= 0 && address < static_cast<long>(instructionMemory.size())) {
            instructionMemory[address] = instruction;
        } else {
            
            std::cerr << "Instruction memory access out of bounds: " << address << std::endl;
        }
    }
    
    // Get instruction memory value
    std::string getInstructionMemory(long address) const {
        if (address >= 0 && address < static_cast<long>(instructionMemory.size())) {
            return instructionMemory[address];
        } else {
            std::cerr << "Instruction memory access out of bounds: " << address << std::endl;
            return "";
        }
    }
    
    // Load program into memory
    bool loadProgram(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Could not open file: " << filename << std::endl;
            return false;
        }
        
        std::string line;
        bool inDataSection = false;
        bool inInstructionSection = false;
        
        while (getline(file, line)) {
            // Remove comments
            size_t commentPos = line.find('#');
            if (commentPos != std::string::npos) {
                line = line.substr(0, commentPos);
            }
            
            // Trim whitespace
            line.erase(0, line.find_first_not_of(" \t"));
            line.erase(line.find_last_not_of(" \t") + 1);
            if (line.empty()) continue;
            
            // Check for section markers
            if (line.find("Begin Data Section") != std::string::npos) {
                inDataSection = true;
                inInstructionSection = false;
                continue;
            } else if (line.find("End Data Section") != std::string::npos) {
                inDataSection = false;
                continue;
            } else if (line.find("Begin Instruction Section") != std::string::npos) {
                inInstructionSection = true;
                inDataSection = false;
                continue;
            } else if (line.find("End Instruction Section") != std::string::npos) {
                inInstructionSection = false;
                continue;
            }
            
            std::istringstream iss(line);
            
            if (inDataSection) {
                long addr, value;
                if (iss >> addr >> value) {
                    setDataMemory(addr, value);
                }
            } else if (inInstructionSection) {
                long addr;
                if (iss >> addr) {
                    // Get the rest of the line as the instruction
                    std::string instruction;
                    std::getline(iss, instruction);
                    // Trim leading whitespace
                    instruction.erase(0, instruction.find_first_not_of(" \t"));
                    setInstructionMemory(addr, instruction);
                }
            }
        }
        
        file.close();
        return true;
    }
    
    // Execute one instruction
    void execute() {
        // Get the current instruction from PC
        
        long pc = dataMemory[0];
        std::string instruction = instructionMemory[pc];
        
        if (instruction.length() != 0) {
        }
        
        // Increment instruction count
        dataMemory[3]++;
        
        // Parse the instruction
        std::string cmd;
        std::vector<long> args;
        
        // Handle SYSCALL specially since it has string arguments
        if (instruction.find("SYSCALL") == 0) {
            std::istringstream iss(instruction);
            std::string syscall, syscallType;
            
            
            if (iss >> syscall >> syscallType) {
                if (syscallType == "PRN") {
                    long arg;
                    if (iss >> arg) {
                        checkMemoryAccess(arg);
                        executeSystemCall("PRN", arg);
                    }
                } else if (syscallType == "HLT") {
                    executeSystemCall("HLT", 0);
                } else if (syscallType == "YIELD") {
                    executeSystemCall("YIELD", 0);
                }
                else {
                    executeSystemCall("None",0);
                }
            }
            else {
                executeSystemCall("None",0);
            }

            // Debug mode 3: Print thread table after system calls
            if (debugMode == 3) {
                std::cerr << "Context Switch Thread " << dataMemory[21] << " -> OS" << std::endl;
                std::cerr << "Thread table of OS: "<< std::endl;
                printThreadTable(0);
            }
            
            return;
        }
        
        parseInstruction(instruction, cmd, args);
        
        // Execute the instruction
        if (instruction.length() == 0) // NULL instruction just skip
        {
            dataMemory[0] = pc + 1; // Increment PC
        }
        else if (cmd == "SET") { // SET B A
            dataMemory[0] = pc + 1; // Increment PC

            if (args.size() >= 2) {
                long value = args[0];
                long target = args[1];
                checkMemoryAccess(target);
                dataMemory[target] = value;

            }
            
        }
        else if (cmd == "CPY") { // CPY A1 A2

            dataMemory[0] = pc + 1; // Increment PC

            if (args.size() >= 2) {
                long src = args[0];
                long dest = args[1];
                checkMemoryAccess(src);
                checkMemoryAccess(dest);
                
                dataMemory[dest] = dataMemory[src];
                
            }
        }
        else if (cmd == "CPYI") { // CPYI A1 A2


            dataMemory[0] = pc + 1; // Increment PC


            if (args.size() >= 2) {
                long src = args[0];
                long dest = args[1];
                checkMemoryAccess(src);
                checkMemoryAccess(dataMemory[src]); // Check indirect access
                checkMemoryAccess(dest);
                dataMemory[dest] = dataMemory[dataMemory[src]];
            }
        }
        else if (cmd == "CPYI2") { // CPYI2 A1 A2 - Copy contents of addres pointed by A1 into address pointed by A2

            dataMemory[0] = pc + 1; // Increment PC

            if (args.size() >= 2) {
                long src = args[0];
                checkMemoryAccess(src);

                long srcI = dataMemory[src];
                checkMemoryAccess(srcI);
                
                long destPtr = args[1];
                checkMemoryAccess(destPtr);

                long dest = dataMemory[destPtr]; // Get the address pointed by A2
                checkMemoryAccess(dest);

                dataMemory[dest] = dataMemory[srcI];
            }
        }
        else if (cmd == "ADD") { // ADD A B
            if (args.size() >= 2) {
                long target = args[0];
                long value = args[1];
                checkMemoryAccess(target);
                dataMemory[target] += value;
            }
            dataMemory[0] = pc + 1; // Increment PC
        }
        else if (cmd == "ADDI") { // ADDI A1 A2
            if (args.size() >= 2) {
                long target = args[0];
                long src = args[1];
                checkMemoryAccess(target);
                checkMemoryAccess(src);
                dataMemory[target] += dataMemory[src];
            }
            dataMemory[0] = pc + 1; // Increment PC
        }
        else if (cmd == "SUBI") { // SUBI A1 A2
            if (args.size() >= 2) {
                long target = args[0];
                long src = args[1];
                checkMemoryAccess(target);
                checkMemoryAccess(src);
                dataMemory[src] = dataMemory[target] - dataMemory[src];
            }
            dataMemory[0] = pc + 1; // Increment PC
        }
        else if (cmd == "JIF") { // JIF A C
            if (args.size() >= 2) {
                long cond = args[0];
                long jmpAddr = args[1];
                checkMemoryAccess(cond);
                if (dataMemory[cond] <= 0) {
                    dataMemory[0] = jmpAddr; // Set PC to jump address
                } else {
                    dataMemory[0] = pc + 1; // Increment PC
                }
            } else {
                dataMemory[0] = pc + 1; // Increment PC
            }
        }
        else if (cmd == "PUSH") { // PUSH A
            if (args.size() >= 1) {
                long src = args[0];
                checkMemoryAccess(src);
                dataMemory[1]--; // Decrement SP (stack grows downwards)
                checkMemoryAccess(dataMemory[1]); // Check stack access
                dataMemory[dataMemory[1]] = dataMemory[src];
            }
            dataMemory[0] = pc + 1; // Increment PC
        }
        else if (cmd == "POP") { // POP A
            if (args.size() >= 1) {
                long dest = args[0];
                checkMemoryAccess(dataMemory[1]); // Check stack access
                checkMemoryAccess(dest);
                dataMemory[dest] = dataMemory[dataMemory[1]];
                dataMemory[1]++; // Increment SP
            }
            dataMemory[0] = pc + 1; // Increment PC
        }
        else if (cmd == "CALL") { // CALL C
            if (args.size() >= 1) {
                long jmpAddr = args[0];
                dataMemory[1]--; // Decrement SP
                checkMemoryAccess(dataMemory[1]); // Check stack access
                dataMemory[dataMemory[1]] = pc + 1; // Push return address
                dataMemory[0] = jmpAddr; // Set PC to jump address
            } else {
                dataMemory[0] = pc + 1; // Increment PC
            }
        }
        else if (cmd == "RET") { // RET
            checkMemoryAccess(dataMemory[1]); // Check stack access
            dataMemory[0] = dataMemory[dataMemory[1]]; // Pop return address to PC
            dataMemory[1]++; // Increment SP
        }
        else if (cmd == "HLT") { // HLT
            halted = true;
        }
        else if (cmd == "USER") { // USER
            dataMemory[0] = dataMemory[50 + dataMemory[21]*40 + 4];
            kernelMode = false;


            if (debugMode == 3)
            {
                if (dataMemory[21] == 10) {
                    
                }
                std::cerr << "Context Switch OS -> Thread " << dataMemory[21] << std::endl;
                std::cerr << "Thread table of thread id " << dataMemory[21] << std::endl;
                printThreadTable(dataMemory[21]);
            }
        }
        else {
            std::cerr << "Unknown instruction: " << cmd << " at PC=" << pc << std::endl;
            halted = true;
        }


        // Debug mode 1: Print memory after each instruction
        if (debugMode == 1) {
            printMemoryState();
        }
        
        // Debug mode 2: Print memory and wait for keypress
        if (debugMode == 2) {
            printMemoryState();
            std::cerr << "Press Enter to continue..." << std::endl;
            std::cin.get();
        }
        
    }
    
    // Print memory state for debugging
    void printMemoryState() {
        std::cerr << "=== MEMORY STATE ===" << std::endl;
        std::cerr << "PC: " << dataMemory[0] << " SP: " << dataMemory[1] << " Executed: " << dataMemory[3] << std::endl;
       
        std::cerr << "22. Thread ID: " << dataMemory[20] << std::endl;
        std::cerr << "22. Thread ID: " << dataMemory[21] << std::endl;
        std::cerr << "22. Thread ID: " << dataMemory[22] << std::endl;
        // std::cerr << "Data Memory (non-zero values):" << std::endl;
        // for (size_t i = 0; i < dataMemory.size(); i++) {
        //     if (dataMemory[i] != 0) {
        //         std::cerr << "  Data[" << i << "] = " << dataMemory[i] << std::endl;
        //     }
        // }
        
        // std::cerr << "Instruction Memory (non-empty values):" << std::endl;
        // for (size_t i = 0; i < instructionMemory.size(); i++) {
        //     if (!instructionMemory[i].empty()) {
        //         std::cerr << "  Instr[" << i << "] = " << instructionMemory[i] << std::endl;
        //     }
        // }
        // std::cerr << "====================" << std::endl;
    }


    // Add this new method for debug mode 3 (thread table printing):
    void printThreadTable(int currentThreadId) {
        std::cerr << "=== THREAD TABLE  ===" << std::endl;
        
        // Get the current thread ID from register 20
        
        // Calculate thread table base address for current thread
        // Thread table starts at 50, each entry is 40 bytes
        long threadTableBase = 50 + (currentThreadId * 40);
        
        std::cerr << "Thread " << currentThreadId << " State:" << std::endl;
        std::cerr << "  Thread ID: " << dataMemory[threadTableBase] << std::endl;
        std::cerr << "  Start Time: " << dataMemory[threadTableBase + 1] << std::endl;
        std::cerr << "  Execution Count: " << dataMemory[threadTableBase + 2] << std::endl;
        std::cerr << "  Thread State: " << dataMemory[threadTableBase + 3] 
                  << " (" << (dataMemory[threadTableBase + 3] == 0 ? "READY" : 
                             dataMemory[threadTableBase + 3] == 1 ? "RUNNING" : "BLOCKED") << ")" << std::endl;
        // std::cerr << "  PC: " << dataMemory[threadTableBase + 4] << std::endl;
        // std::cerr << "  SP: " << dataMemory[threadTableBase + 5] << std::endl;
        // std::cerr << "  Block Counter: " << dataMemory[threadTableBase + 6] << std::endl;
        
        // Print saved registers (2-20)
        std::cerr << "  Saved Registers:" << std::endl;
        for (int reg = 2; reg <= 20; reg++) {
            long regAddr = threadTableBase + 10 + reg;  // First register starts at offset 10
            std::cerr << "    reg->" << reg << " : " << dataMemory[regAddr] << std::endl;
        }
        
        std::cerr << "===================" << std::endl;
    }

};

// Main function for testing
int main(int argc, char* argv[]) {
    
    std::string filename = "./v2.txt";
    int debugMode = 0;  // Default debug mode
    
    // Parse command line arguments for debug flag
//    for (int i = 2; i < argc; i++) {
//        if (std::string(argv[i]) == "-D" && i + 1 < argc) {
//            debugMode = std::stoi(argv[i + 1]);
//            if (debugMode < 0 || debugMode > 3) {
//                std::cerr << "Invalid debug mode. Must be 0, 1, 2, or 3." << std::endl;
//                return 1;
//            }
//        }
//    }
    
    // Create CPU and load program
    CPU cpu(11000, 11000);
    cpu.setDebugMode(debugMode);
    
    if (!cpu.loadProgram(filename)) {
        return 1;
    }
    
    std::cout << "Running in debug mode " << debugMode << std::endl;
    
    // Run simulation
    while (!cpu.isHalted()) {
        // std::cout << "aaaa" << std::endl;
        cpu.execute();
    }
    
    std::cout << "Program terminated." << std::endl;
    
    // Debug mode 0: Print memory only after halt
    if (debugMode == 0) {
        cpu.printMemoryState();
    }
    
    return 0;
}
