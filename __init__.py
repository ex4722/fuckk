from binaryninja import *
from .workflow import FuckkWorkFlow

KERN_EMERG= "0"
KERN_ALERT= "1"
KERN_EMERG= "0"
KERN_ALERT= "1"
KERN_CRIT= "2"
KERN_ERR= "3"
KERN_WARNING= "4"
KERN_NOTICE= "5"
KERN_INFO= "6"
KERN_DEBUG= "7"
KERN_DEFAULT= ""

# bv = load("./")

# DataRander does not work unless each string has a label which we should do but is kinda stupid for string tables
# class KernelStringDataRenderer(DataRenderer):
#         def __init__(self):
#                 DataRenderer.__init__(self)
#         def perform_is_valid_for_data(self, ctxt, view, addr, type, context):
#             print(f"Called at {hex(addr)} with type {type}")
#             if type == int and bv.get_string_at(addr + 1) != None:
#                 print("FOUND SHIT")
#                 return True
#             return False 
#         def perform_get_lines_for_data(self, ctxt, view, addr, type, prefix, width, context):
#                 prefix.append(InstructionTextToken(InstructionTextTokenType.TextToken, "I'm in ur BAR"))
#                 return [DisassemblyTextLine(prefix, addr)]
#         def __del__(self):
#                 pass
#
# KernelStringDataRenderer().register_type_specific()

def do_nothing(bv):
	show_message_box("Do Nothing", "Congratulations! You have successfully done nothing.\n\n" +
					 "Pat yourself on the back.", MessageBoxButtonSet.OKButtonSet, MessageBoxIcon.ErrorIcon)

# prink is most commenly a extern symbol for kernel modules
def find_printk_in_extern() -> CoreSymbol | None: 
    extern = bv.sections['.extern']
    assert bv.arch is not None
    for addr in range(extern.start, extern.end, bv.arch.address_size):
        symbol = bv.get_symbol_at(addr)
        if(symbol != None):
            if(symbol.name == 'printk'):
                return symbol 
    return None

def main():
    printk = find_printk_in_extern()
    if(printk == None):
        log_error("Prink not found")
        return -1
    # for caller in bv.get_callers(printk.address):
    for caller in bv.get_callers(printk.address):
        assert caller.hlil is not None
        string = bv.get_string_at(caller.hlil.params[0].constant + 1)
        kernel_soh = bv.read(caller.hlil.params[0].constant,1)
        if kernel_soh != 1:
            # KERN_Default here
            continue

        if string != None:
            # String found here, assume first byte is \x01 and next is log level
            string = string.raw
            log_level = int(chr(string[0]))
            string = string[1:]
            print(f"{log_level} {string}")


PluginCommand.register("Useless Plugin", "Basically does nothing", do_nothing)
FuckkWorkFlow.register()
