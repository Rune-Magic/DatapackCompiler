import beet, mecha
import os, sys, shutil
import commands
from templates import *

def beet_default(ctx: beet.Context):
    depots = commands.Depots()
    parser = mecha.Mecha()
    name = ctx.project_id
    functions = ""
    compiled_list = ""
    to_compile = []
    for function_id, function in ctx.data.functions.items():
        if "#no_compile" not in function.lines:
            to_compile.append((function_id, function))
            compiled_list += f'"{function_id}",\n'
    for function_id, function in to_compile:
        ast = parser.parse(function)
        macros = []
        body = ""
        for command in ast.commands:
            output, out_macros, _ = commands.compile(command, parser, depots, to_compile)
            for macro in out_macros:
                if macro in macros: continue
                macros.append(macro)
            body += output
        functions += function_template.format(
            function=function_id, 
            body=body
        )
        function_execution = f"_function__{ctx.project_id} \"{function_id}\" {{"
        if (len(macros) > 0): 
            function_execution = "$" + function_execution
            for macro in macros:
                function_execution += f"\"{macro}\": $({macro}), "
            function_execution = function_execution[:-2]
        function.lines = [function_execution + "}"]
    shutil.rmtree("out")
    shutil.copytree("template", "out")
    os.makedirs(os.path.join("out/src/main/java/datapack/", name))
    with open("out/src/main/java/datapack/" + name + "/EntryPoint.java", "x") as f:
        if len(compiled_list) > 0:
            compiled_list = compiled_list[:-2]
        else:
            print("WARNING: nothing was compiled")
        f.write(entry_point_template.format(
            name=name,
            commands=functions,
            depots=depots.package(),
            to_compile=compiled_list
        ))
    with open("out/src/main/resources/fabric.mod.json", "x") as f:
        f.write(mod_config_template.format(
            name=name,
            desc=ctx.project_description,
            title=ctx.project_name,
            version=ctx.project_version,
            author=ctx.project_author
        ))        
