from binaryninja import * 
from binaryninja import core
from typing import cast

LOG_LEVELS = {
    0: "pr_emerg",
    1: "pr_alert",
    2: "pr_crit",
    3: "pr_err",
    4: "pr_warning",
    5: "pr_notice",
    6: "pr_info",
    7: "pr_debug",
}

def find_printk_in_extern(bv: BinaryView) -> CoreSymbol | None: 
    extern = bv.sections['.extern']
    assert bv.arch is not None
    for addr in range(extern.start, extern.end, bv.arch.address_size):
        symbol = bv.get_symbol_at(addr)
        if(symbol != None):
            if(symbol.name == 'printk'):
                return symbol 
    return None

# Function creates macros like pr_error and pr_assert by creating new virtual segment and writing symbols in 
def create_printk_macros(bv: BinaryView)-> Dict[int, int]:
    function_table = {}
    # Allocates a virtual segment after current last segment for 10 function pointers
    segment_start = bv.segments[-1].end 
    segment_length = len(LOG_LEVELS) * bv.arch.address_size
    bv.add_user_segment(segment_start, segment_length, 0 ,0, SegmentFlag.SegmentContainsData)
    bv.add_user_section(".macro", segment_start, segment_length, SectionSemantics.ExternalSectionSemantics)
    for num, macro_name in  LOG_LEVELS.items():
        bv.define_auto_symbol(Symbol(SymbolType.ExternalSymbol, segment_start, macro_name, binding=SymbolBinding.GlobalBinding))
        function_table[num] = segment_start
        # bv.add_function(segment_start, bv.platform)
        # FUCKING FUNCTIONS NOT RESOLVED IN VIEW
        segment_start += bv.arch.address_size
    return function_table

def extract_level_and_fmstr_from_instruction(bv: BinaryView, mlil: MediumLevelILCall) -> tuple[int, int]:
    string = bv.get_string_at(mlil.params[0].value.value+1)
    assert string is not None
    full_string = string.raw
    # Add one for the \x01 byte in front
    log_level, fmstr= int(chr(full_string[0])), full_string[1:]
    return (log_level, mlil.params[0].value.value+2)

def fuckk_printk(analysis_context: core.BNAnalysisContext):
    func:Function = Function(handle=core.BNAnalysisContextGetFunction(analysis_context))
    bv:BinaryView = func.view
    printk = find_printk_in_extern(bv)
    assert printk is not None
    if not bv.get_section_by_name(".macro"):
        print("CREATING MACRO")
        create_printk_macros(bv)
    for idx in range(len(func.mlil)-1):
        mlil_instr:MediumLevelILInstruction = func.mlil[idx]
        if mlil_instr.operation == MediumLevelILOperation.MLIL_CALL:
            mlil_instr= cast(MediumLevelILCall, mlil_instr)
            if(mlil_instr.dest.value == printk.address):
                print(f"FOUND IT BITCH @ {mlil_instr}")
                log_level, fmstr= extract_level_and_fmstr_from_instruction(bv, mlil_instr) 
                # Constructing new mlil 
                output_len, output_expr, dest, params_len, _ = mlil_instr.instr.operands

                log_function = bv.get_symbols_by_name(LOG_LEVELS[log_level])[0].address
                mlil_func = func.mlil.expr(MediumLevelILOperation.MLIL_CONST_PTR, ExpressionIndex(log_function))
                mlil_const_ptr = func.mlil.expr(MediumLevelILOperation.MLIL_CONST_PTR, ExpressionIndex(fmstr))
                call_param = func.mlil.expr(MediumLevelILOperation.MLIL_CALL_PARAM,2,func.mlil.add_operand_list([mlil_const_ptr]))

                mlil_intrinsic = func.mlil.expr(MediumLevelILOperation.MLIL_CALL,output_len, output_expr, mlil_func, params_len, call_param-1)
                print(f"Replacing {func.mlil[idx]} with {mlil_intrinsic} @ {hex(mlil_instr.address)}")
                func.mlil.replace_expr(func.mlil[idx],mlil_intrinsic)
    func.mlil.generate_ssa_form()


FuckkWorkFlow = Workflow().clone("FuckkWorkflow")
FuckkWorkFlow.register_activity(Activity("Fuckk", action=fuckk_printk))
FuckkWorkFlow.insert("core.function.analyzeTailCalls", ['Fuckk'])
