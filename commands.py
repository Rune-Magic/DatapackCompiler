import mecha
import builtins
import inspect
import re as regex
from typing import Iterator, Callable, Any, Literal, overload
from dataclasses import dataclass, field

"""Can be used for anything that requires unique names"""
counter: int = 0

@dataclass
class Depot:
    contents: dict[str, str] | dict[str, tuple[str, Any]] = field(default_factory=dict)
    sep: str = ""
    
    def __getitem__(self, name: str) -> str | tuple[str, Any]:
        return self.contents[name]
    
    def __setitem__(self, name: str, value: str | tuple[str, Any]) -> None:
        self.contents[name] = value
        
    def __contains__(self, obj) -> bool:
        return obj in self.contents
    
    def package(self) -> str:
        contents = ""
        for key, content in self.contents.items():
            if isinstance(content, tuple):
                content = content[0]
            contents += f"// {key}\n" + content + self.sep
        if len(self.sep) > 0 and len(contents) > 0: contents = contents[:-len(self.sep)]
        return contents.rstrip()

@dataclass
class Depots:
    commands = Depot()
    resource_location = Depot()
    nbt = Depot()
    range_double = Depot()
    range_int = Depot()
    component = Depot()
    selector = Depot()
    block_predicate = Depot()
    static_nbt = Depot()
    static_component = Depot()
    static_selector = Depot()
    static_block_predicate = Depot()
    
    def package(self) -> str:
        return f"""
        /* resource locations */
        {self.resource_location.package()}
        
        /* nbt tags */
        {self.nbt.package()}
        
        /* min max bounds */
        {self.range_int.package()}
        {self.range_double.package()}
        
        /* components */
        {self.component.package()}
        
        /* selectors */
        {self.selector.package()}
        
        /* block predicates */
        {self.block_predicate.package()}
        
        static {{
            /* nbt */
            {self.static_nbt.package()}
            
            /* components */
            {self.static_component.package()}
            
            /* selectors */
            {self.static_selector.package()}
            
            /* block predicates */
            {self.static_block_predicate.package()}
        }}
        
        {self.commands.package()}
        """

def compile(command: mecha.AstCommand, parser: mecha.Mecha, depots: Depots, functions: list[tuple]) -> tuple[str, list[str], "Walker"]:
    global counter
    key = parser.serialize(command)
    if key in depots.commands:
        return depots.commands[key][1], depots.commands[key][2], depots.commands[key][3]
    name = f"command_{counter}"
    counter += 1
    walker = Walker(
        iter(command.identifier.split(':')),
        iter(command.arguments),
        command,
        depots,
        parser,
        functions,
    )
    try:
        walker.next(
            say=lambda: say(walker),
            mecha=lambda: macro(walker),
            tp=lambda: tp(walker),
            teleport=lambda: tp(walker),
            kill=lambda: kill(walker),
            give=lambda: give(walker),
            function=lambda: function(walker),
            execute=lambda: execute(walker),
        )
    except Exception as e:
        print(type(e).__name__, e, sep=": ")
        if not isinstance(e, (NotImplementedError, KeyError)):
            raise e
        walker.output = f"""
            // {type(e)}: {e}
            /*\n{walker.command.dump(exclude=("location", "end_location"))}
            */
            dispatcher.execute(dispatcher.parse("%s", source));
            """ %parser.serialize(walker.command).replace('\\', '\\\\').replace('"', '\\"')
        walker.reqiures_dispatcher = True
    out = regex.sub(r"\n\s*?\n", "\n", walker.output)
    name += "(CommandSourceStack source"
    if walker.reqiures_dispatcher: name += ", CommandDispatcher<CommandSourceStack> dispatcher"
    if walker.reqiures_macros: name += ", CompoundTag marcos"
    name += ")"
    walker.output = f"""
        private static {'MaybeReturn' if walker.returns == Maybe else 'int'} {name} throws CommandSyntaxException {{
            int result = 0;
            {out}
            return {'new MaybeReturn(false, ' if walker.returns == Maybe else '('}result);
        }}
    \n""".lstrip()
    name = name.replace("CommandSourceStack ", "", 1).replace("CommandDispatcher<CommandSourceStack> ", "", 1).replace("CompoundTag ", "", 1)
    if walker.returns == True:
        name = "return " + name
    elif walker.returns == Maybe:
        name = f"if ({name}.out() instanceof Integer integer) return integer;"
    name += f"; // {key}\n"
    depots.commands[key] = (walker.output, name, walker.macros, walker)
    return (name, walker.macros, walker)

Maybe: Literal["Maybe"] = "Maybe"
@dataclass
class Walker:
    identifiers: Iterator[str]
    nodes: Iterator[mecha.AstNode]
    command: mecha.AstCommand
    depots: Depots
    parser: mecha.Mecha
    functions: list[tuple]
    
    macros: list[str] = field(default_factory=list)
    output: str = ""
    reqiures_dispatcher: bool = False
    reqiures_macros: bool = False
    returns: bool | Literal["Maybe"] = False
    
    chain_args: dict[str, Callable] = field(default_factory=dict)
    
    def next(self, **functions: dict[str, Callable]) -> Any:
        functions.update(self.chain_args)
        identifier = builtins.next(self.identifiers, None)
        if identifier is None:
            return
        f = functions[identifier]
        debug = "\n\t\t\t\t// %s\n"
        if len(inspect.getfullargspec(f).args) > 0:
            node = builtins.next(self.nodes)
            self.output += debug %self.parser.serialize(node)
            return f(node)
        else:
            self.output += debug %identifier
            return f()

def range_doubles(node: mecha.AstRange, walker: Walker) -> str:
    key = walker.parser.serialize(node)
    name = f"Range_Double_{str(node.min).replace('.', 'point').replace('-', 'negative')}__{str(node.max).replace('.', 'point').replace('-', 'negative')}"
    if key in walker.depots.range_double.contents:
        return name
    min = "Optional.empty()"
    max = "Optional.empty()"
    minSq = "Optional.empty()"
    maxSq = "Optional.empty()"
    if node.min is not None:
        min = f"Optional.of((double) {node.min})"
        minSq = f"Optional.of((double) {node.min ** 2})"
    if node.max is not None:
        max = f"Optional.of((double) {node.max})"
        maxSq = f"Optional.of((double) {node.max ** 2})"
    walker.depots.range_double[key] = f"private static final MinMaxBounds.Doubles {name} = new MinMaxBounds.Doubles({min}, {max}, {minSq}, {maxSq});\n"
    return name

def range_ints(node: mecha.AstRange, walker: Walker) -> str:
    key = walker.parser.serialize(node)
    name = f"Range_Int_{str(node.min).replace('-', 'negative')}__{str(node.max).replace('-', 'negative')}"
    if key in walker.depots.range_int.contents:
        return name
    min = "Optional.empty()"
    max = "Optional.empty()"
    minSq = "Optional.empty()"
    maxSq = "Optional.empty()"
    if node.min is not None:
        min = f"Optional.of((int) {node.min})"
        minSq = f"Optional.of((long) {node.min ** 2})"
    if node.max is not None:
        max = f"Optional.of((int) {node.max})"
        maxSq = f"Optional.of((long) {node.max ** 2})"
    walker.depots.range_int[key] = f"private static final MinMaxBounds.Ints {name} = new MinMaxBounds.Ints({min}, {max}, {minSq}, {maxSq});\n"
    return name

def resource_location(node: mecha.AstResourceLocation, walker: Walker) -> str:
    key = walker.parser.serialize(node)
    value = ""
    name = "ResourceLocation_"
    if node.namespace is None:
        value = f'ResourceLocation.withDefaultNamespace("{node.path}")'
        name += str(node.path).replace("/", "SLASH").replace(".", "DOT")
    else:
        value = f'ResourceLocation.fromNamespaceAndPath("{node.namespace}", "{node.path}")'
        name += f"{node.namespace}_{node.path}".replace("/", "SLASH").replace(".", "DOT")
    walker.depots.resource_location[key] = f"private static final ResourceLocation {name} = {value};\n"
    return name

def nbt(node: mecha.AstNbtValue, walker: Walker, *, return_type = False) -> str:
    """
    Args:
        return_type: Whether or not to return the type of the nbt value.
    """
    global counter
    key = walker.parser.serialize(node)
    if key in walker.depots.nbt.contents:
        return walker.depots.nbt[key][1]
    counter += 1
    def eval(node: mecha.AstNbtValue, tmp = True) -> tuple[str, str]:
        global counter
        tmp = 'var ' if tmp else ''
        name = None
        static = ""
        type = None
        if isinstance(node, mecha.AstNbtBool):
            name = f"ByteTag.valueOf({str(int(node.value) > 0).lower()})"
            type = "ByteTag"
        elif isinstance(node, mecha.AstNbtCompound):
            type = "CompoundTag"
            name = "CompoundTag_%i" %counter
            counter += 1
            static += f"{tmp}{name} = new CompoundTag();\n"
            for entry in node.entries:
                symbol, init, _ = eval(entry.value)
                static += init
                static += f'{name}.put("{entry.key.value}", {symbol});\n'
        elif isinstance(node, mecha.AstNbtList):
            type = "ListTag"
            name = "ListTag_%i" %counter
            counter += 1
            static += f"{tmp}{name} = new ListTag();\n"
            for element in node.elements:
                symbol, init, _ = eval(element)
                static += init
                static += f"{name}.add({symbol});\n"
        else:
            value = None
            match node.value.__class__.__name__:
                case "Int": 
                    value = f"IntTag.valueOf({int(node.value)})"
                    type = "IntTag"
                case "Byte": 
                    value = f"ByteTag.valueOf((byte) {int(node.value)})"
                    type = "ByteTag"
                case "Long": 
                    value = f"LongTag.valueOf({int(node.value)}L)"
                    type = "LongTag"
                case "Float": 
                    value = f"FloatTag.valueOf({float(node.value)}f)"
                    type = "FloatTag"
                case "Double": 
                    value = f"DoubleTag.valueOf({float(node.value)})"
                    type = "DoubleTag"
                case "Short": 
                    value = f"ShortTag.valueOf({int(node.value)}s)"
                    type = "ShortTag"
                case "String": 
                    value = f'StringTag.valueOf("{str(node.value)}")'
                    type = "StringTag"
                case otherwise: 
                    raise NotImplemented(f"couldn't find nbt type {otherwise}")
            name = f"{type}_{counter}"
            counter += 1
            static += f"{tmp}{name} = {value};\n"
        return (name, static, type)
    symbol, init, type = eval(node, tmp=False)
    walker.depots.nbt[key] = (f"private static final {type} {symbol};\n", symbol)
    walker.depots.static_nbt[key] = init
    if return_type:
        return (symbol, type)
    return symbol
    
@overload
def vec3(position: str, rotation: str, node: mecha.AstVector3, /, *, vec3i = False) -> str: ...
    
@overload
def vec3(node: mecha.AstVector3, /, *, vec3i = False) -> str: ...

def vec3(*args, vec3i = False) -> str:
    position: str = "source.getAnchor().apply(source)"
    rotation: str = "source.getRotation()"
    node: mecha.AstVector3 = None
    if len(args) > 1:
        position = args[0]
        rotation = args[1]
        node = args[2]
    else:
        node = args[0]
    if node.x.type == "local":
        return f"{'toVec3i(' if vec3i else ''}{position}.add(Vec3.directionFromRotation({rotation}).multiply(new Vec3({node.x.value}, {node.y.value}, {node.z.value}))){')' if vec3i else ''}"
    else:
        def do(coord: mecha.AstCoordinate, c: str):
            relative, absolute = "0", f"{'(int) ' if vec3i else ''}{position}.{c}()"
            if coord.type == "absolute":
                absolute = coord.value
                if vec3i: absolute = int(absolute)
            elif coord.type == "relative":
                relative = coord.value
                if vec3i: relative = int(relative)
            else: raise
            return (relative, absolute)
        x = do(node.x, "x")
        y = do(node.y, "y")
        z = do(node.z, "z")
        return f"new Vec3{'i' if vec3i else ''}({x[1]} + {x[0]}, {y[1]} + {y[0]}, {z[1]} + {z[0]})"

def vec2(rotation: str, node: mecha.AstVector2):
    def do(coord: mecha.AstCoordinate, c: str):
        relative, absolute = "0", f"{rotation}.{c}()"
        if coord.type == "absolute":
            absolute = coord.value
        elif coord.type == "relative":
            relative = coord.value
        else: raise
        return (relative, absolute)
    x = do(node.x, "x")
    y = do(node.y, "y")
    return f"new Vec2({x[1]} + {x[0]}, {y[1]} + {y[0]})"
            
def selector(node: mecha.AstNode, walker: Walker, single: bool, player = False) -> str:
    global counter
    key = walker.parser.serialize(node)
    if key in walker.depots.selector:
        getMethod = ""
        if single:
            if not player:
                getMethod = "findSingleEntity"
            else:
                getMethod = "findSinglePlayer"
        else:
            if not player:
                getMethod = "findEntities"
            else:
                getMethod = "findPlayers"
        return f"{walker.depots.selector[key][1]}.{getMethod}(source)"
    name = "Selector_%i" %counter
    counter += 1
    maxResults = "EntitySelector.INFINITE"
    includesEntities = "false" if player else "true"
    worldLimited = "false"
    predicates = ""
    range = "MinMaxBounds.Doubles.ANY"
    x = "old.x"
    y = "old.y"
    z = "old.z"
    dx = None
    dy = None
    dz = None
    order = "null"
    currentEntity = "false"
    playerName = "null"
    entityUUID = "null"
    type = "null"
    usesSelector = "false"
    def add_predicate(predicate: str, inverted = False) -> None:
        nonlocal predicates
        invert = "!" if inverted else ""
        predicates += f'entity -> {invert}{predicate}, '
    def add_player_predicate(predicate: str, inverted = False, before = "") -> None:
        nonlocal predicates
        invert = "!" if inverted else ""
        predicates +=  f"""entity -> {{
            if (entity instanceof ServerPlayer) {{
                {before}
                return {invert}{predicate};
            }}
            return false;
        }}, """
    if isinstance(node, mecha.AstSelector):
        usesSelector = "true"
        match node.variable:
            case "a":
                includesEntities = "false"
            case "e":
                pass
            case "p":
                includesEntities = "false"
                maxResults = "1"
                worldLimited = "true"
                order = "Sort.NEAREST"
            case "r":
                includesEntities = "false"
                order = "Sort.RANDOM"
            case "s":
                currentEntity = "true"
            case "n":
                maxResults = "1"
                worldLimited = "true" 
                order = "Sort.NEAREST"
        for arg in node.arguments:
            match arg.key.value:
                case "x":
                    x = arg.value.value
                    worldLimited = "true"
                case "y":
                    y = arg.value.value
                    worldLimited = "true"
                case "z":
                    z = arg.value.value
                    worldLimited = "true"
                case "dx":
                    dx = arg.value.value
                    worldLimited = "true"
                case "dy":
                    dy = arg.value.value
                    worldLimited = "true"
                case "dz":
                    dz = arg.value.value
                    worldLimited = "true"
                case "tag":
                    add_predicate(f'entity.getTags().contains("{arg.value.value}")', arg.inverted)
                case "distance":
                    range = range_doubles(arg.value, walker)
                    worldLimited = "true"
                case "x_rotation":
                    add_predicate(f'{range_doubles(arg.value, walker)}.matches(entity.getXRot())')
                case "y_rotation":
                    add_predicate(f'{range_doubles(arg.value, walker)}.matches(entity.getYRot())')
                case "type":
                    if (not arg.inverted) and arg.value.path == "player" and (arg.value.namespace == None or arg.value.namespace == "minecraft"):
                        includesEntities = "false"
                    else:
                        end = ""
                        if not arg.value.is_tag:
                            end = (f"HolderSet.direct(Holder.direct(BuiltInRegistries.ENTITY_TYPE.get({resource_location(arg.value, walker)})))")
                        else:
                            end = (f"TagKey.create(Registries.ENTITY_TYPE, {resource_location(arg.value, walker)})")
                        add_predicate(f"entity.getType().is({end})", arg.inverted)
                case "gamemode":
                    add_player_predicate(f'entity.gameMode.getGameModeForPlayer() == GameType.byName("{arg.value.value}")', arg.inverted)
                case "advancements":
                    for match in arg.value.advancements:
                        if isinstance(match.value, mecha.AstBool):
                            add_player_predicate(f'entity.getAdvancements().getOrStartProgress(Objects.requireNonNull(entity.getServer().getAdvancements().tree().get({resource_location(match.key, walker)})).holder()).isDone()', match.value.value)
                        else: 
                            completed = ""
                            unfinished = ""
                            for match_predicate in match.value: 
                                out = ""
                                if match_predicate.value.value:
                                    if len(completed) > 0:
                                        completed += ", "
                                    completed += out
                                else:
                                    if len(unfinished) > 0:
                                        unfinished += ", "
                                    unfinished += out
                            add_player_predicate(before=f"""
                                final boolean[] valid = {{true}};
                                var completed = List.of({completed});
                                var unfinished = List.of({unfinished});
                                entity.getAdvancements().getOrStartProgress(Objects.requireNonNull(entity.getServer().getAdvancements().tree().get({resource_location(match.key, walker)})).holder()).getCompletedCriteria().forEach(it -> {{
                                    if (!valid[0]) return;
                                    valid[0] = completed.contains(it) || !unfinished.contains(it);
                                }});
                                """, predicate="valid"
                            )
                case "predicate":
                    raise NotImplementedError("predicates are not yet implemented (and probably never will be)") # tried for 3 hours
                case "name":
                    add_predicate(f'entity.getName().getString().equals("{arg.value.value}")', arg.inverted)
                case "level":
                    add_player_predicate(f'{range_doubles(arg.value, walker)}.matches(entity.experienceLevel)')
                case "sort":
                    match arg.value.value:
                        case "nearest": 
                            order = "Sort.NEAREST"
                            worldLimited = "true"
                        case "furthest": 
                            order = "Sort.FURTHEST"
                            worldLimited = "true"
                        case "arbitrary": 
                            order = "Sort.ARBITRARY"
                        case "random": 
                            order = "Sort.RANDOM"
                        case _: 
                            raise
                case "nbt":
                    add_predicate(f"nbtMatches(new EntityDataAccessor(entity).getData(), {nbt(arg.value, walker)})")
                case "scores":
                    for score in arg.value.scores:
                        add_predicate(f'{range_ints(score.value, walker)}.matches(entity.getServer().getScoreboard().getPlayerScoreInfo(entity, entity.getServer().getScoreboard().getObjective("{score.key.value}")).value())')
                case "team":
                    if arg.value.value is None:
                        add_predicate(f"entity.getTeam() == null")
                    else:
                        add_predicate(f'entity.getTeam() != null && entity.getTeam().getName().equals("{arg.value.value}")')
                case thing:
                    raise NotImplemented("selector argument '" + thing + "' is not implemented")
    elif isinstance(node, mecha.AstPlayerName):
        playerName = '"' + node.value + '"'
    elif isinstance(node, mecha.AstUUID):
        entityUUID = f'UUID.fromString("{node.value}")'
    else:
        raise ValueError(f"could not match selector {node}")
    player = includesEntities == "false"
    getMethod = ""
    if single:
        if not player:
            getMethod = "findSingleEntity"
        else:
            getMethod = "findSinglePlayer"
    else:
        if not player:
            getMethod = "findEntities"
        else:
            getMethod = "findPlayers"
    aabb = "null"
    if dx is not None or dy is not None or dz is not None:
        if dx is None: dx = 0
        if dy is None: dy = 0
        if dz is None: dz = 0
        aabb = f"new AABB(Vec3.ZERO, new Vec3({dx+1}, {dy+1}, {dz+1}))"
    if (len(predicates) > 0):
        predicates = predicates[:-2]
    walker.depots.selector[key] = (f"private static final EntitySelector {name};\n", name)
    walker.depots.static_selector[key] = f"""{name} = new EntitySelector(
                {maxResults}, {includesEntities}, {worldLimited}, List.of({predicates}),
                {range}, old -> new Vec3({x}, {y}, {z}), {aabb}, {order}, {currentEntity},
                {playerName}, {entityUUID}, {type}, {usesSelector}
            );\n"""
    return f"{name}.{getMethod}(source)"

def entity_anchor(node: mecha.AstEntityAnchor) -> str:
    return f"EntityAnchorArgument.Anchor.{node.value.upper()}"

def components(nodes: mecha.AstChildren[mecha.AstItemComponent], walker: Walker) -> str:
    global counter
    if len(nodes) == 0:
        return "DataComponentPatch.EMPTY"
    key = ""
    for node in nodes:
        key += walker.parser.serialize(node) + "\t"
    if key in walker.depots.component.contents:
        return walker.depots.component[key][1]
    name = "Components_%i" %counter
    builder = name + "_Builder"
    counter += 1
    static = f"var {builder} = DataComponentPatch.builder();\n"
    for node in nodes:
        data, type = nbt(node.value, walker, return_type=True)
        static += f"{builder}.set((DataComponentType<{type}>) BuiltInRegistries.DATA_COMPONENT_TYPE.get({resource_location(node.key, walker)}), {data});\n"
    static += f"{name} = {builder}.build();\n"
    walker.depots.component[key] = (f"private static final DataComponentPatch {name};", name)
    walker.depots.static_component[key] = static
    return name
    
def item_stack(node: mecha.AstItemStack, walker: Walker, *, count: int) -> str:
    return f"new ItemStack(Holder.direct(BuiltInRegistries.ITEM.get({resource_location(node.identifier, walker)})), {count}, {components(node.arguments, walker)})"

def access_data(walker: Walker) -> str:
    output = None
    def block():
        nonlocal output
        block_pos = None
        def sourcePos(node: mecha.AstVector3):
            nonlocal block_pos
            block_pos = vec3("source.getAnchor().apply(source)", "source.getRotation()", node, vec3i=True)
        walker.next(sourcePos=sourcePos)
        output = f"new BlockDataAccessor(source.getLevel().getBlockEntity(new BlockPos({block_pos})), new BlockPos({block_pos})).getData()"
    def entity():
        nonlocal output
        source_entity = None
        def source(node: mecha.AstNode):
            nonlocal source_entity
            source_entity = selector(node, walker, True)
        walker.next(source=source)
        output = f"new EntityDataAccessor({source_entity}).getData()"
    def storage():
        nonlocal output
        source_storage = None
        def source(node: mecha.AstResourceLocation):
            nonlocal source_storage
            source_storage = resource_location(node, walker)
        walker.next(source=source)
        output = f"source.getServer().getCommandStorage().get({source_storage})"
    walker.next(block=block, entity=entity, storage=storage)
    return output

def nbt_path(root: str, node: mecha.AstNbtPath, walker: Walker, *, single: bool):
    for component in node.components:
        pack = True
        if isinstance(component, mecha.AstNbtPathKey):
            root = f'((CompoundTag) {root}).get("{component.value}")'
        elif isinstance(component, mecha.AstNbtCompound):
            root = f"returnIfMatches((Tag) {root}, {nbt(component, walker)})"
        elif isinstance(component, mecha.AstNbtPathSubscript):
            if component.index is None:
                if single:
                    root = f"((ListTag) {root}).get(0)"
                pack = False
            elif isinstance(component.index, mecha.AstNumber):
                root = f"((ListTag) {root}).get({component.index.value})"
            elif isinstance(component.index, mecha.AstNbtCompound):
                root = f"((ListTag) {root}).stream().filter(tag -> tag instanceof CompoundTag && nbtMatches(tag, {nbt(component.index, walker)})).collect(Collectors.toList())"
                if single:
                    root = f"((ListTag) {root}).get(0)"
                pack = False
            else: raise
    root = f"Objects.requireNonNull({root})"
    if pack and not single:
        return f"List.of({root})"
    return root

def facing(walker: Walker):
    def facingLocation(node: mecha.AstVector3):
        value = vec3("source.getAnchor().apply(source)", "source.getRotation()", node)
        walker.output += f"source = source.facing({value});\n"
    def entity():
        def facingEntity(node: mecha.AstNode):
            value = selector(node, walker, True)
            anchor = "EntityAnchorArgument.Anchor.FEET"
            def facingAnchor(node: mecha.AstEntityAnchor):
                nonlocal anchor
                anchor = entity_anchor(node)
            walker.next(facingAnchor=facingAnchor)
            walker.output += f"source = source.facing({value}, {anchor});\n"
        walker.next(facingEntity=facingEntity)
    walker.next(facingLocation=facingLocation, entity=entity)
    
def heightmap(node: mecha.AstHeightmap) -> str:
    return f"Heightmap.Types.{node.value.upper()}"

def block_predicate(node: mecha.AstBlock, walker: Walker) -> str:
    global counter
    key = walker.parser.serialize(node)
    if key in walker.depots.block_predicate:
        return walker.depots.block_predicate[key][1]
    name = f"BlockPredicate_{counter}"
    counter += 1
    walker.depots.block_predicate[key] = (f"private static BlockPredicate {name};\n", name)
    out = "{"
    resource = resource_location(node.identifier, walker)
    if node.identifier.is_tag:
        out += f"""
            var blocks = TagKey.create(Registries.BLOCK, {resource});
            var stateDefintion = BuiltInRegistries.BLOCK.getTagOrEmpty(blocks).iterator().next().unwrap().right().orElseThrow().getStateDefinition();
        """
    else:
        out += f"""
            var blocks = BuiltInRegistries.BLOCK.get({resource});
            var stateDefintion = blocks.getStateDefinition();
        """
    out += f"{name} = BlockPredicate.Builder.block().of(blocks)"
    if len(node.block_states) > 0:
        out += ".setProperties(StatePropertiesPredicate.Builder.properties()"
        for state in node.block_states:
            out += f'\n.hasProperty(stateDefintion.getProperty("{state.key}"), "{state.value}"))'
        out += ")"
    if node.data_tags is not None:
        out += f".hasNbt({nbt(node.data_tags, walker)})"
    out += ".build();\n}\n"
    return name

def run_function(node: mecha.AstResourceLocation, walker: Walker, *, on_error = "throw new RuntimeException(e);", macros = "new CompoundTag();", post_exec = "") -> str:
    call: str = None
    location = resource_location(node, walker)
    if node.is_tag:
        call = f"""
            source.getServer().getFunctions().getTag({location}).forEach(func -> {{
                int executionResult;
                try {{
                    if (COMPILED.contains(func.id().toString())) {{
                        executionResult = function(source, func.id().toString(), {macros}, dispatcher);
                    }} else {{
                        executionResult = func.instantiate({macros}, dispatcher);
                    }}
                }} catch (Exception e) {{
                    {on_error}
                }}
                {post_exec}
            }});
            """
    else:
        call = "int executionResult;\ntry {{\n"
        raw = walker.parser.serialize(node)
        for func in walker.functions:
            if func[0] == raw:
                call += f'executionResult = function(source, "{raw}", {macros}, dispatcher);\n'
                break
        else:
            call += f'executionResult = source.getServer().getFunctions().get({location}).orElseThrow().instantiate({macros}, dispatcher);'
        call += f"""
            }} catch (Exception e) {{
                {on_error}
            }}
            {post_exec}
        """
    return call

##################

def macro(walker: Walker):
    command = ""
    macros = []
    for child in walker.command.arguments:
        if isinstance(child, mecha.AstMacroLineText):
            command += f'"{child.value}" + '
        elif isinstance(child, mecha.AstMacroLineVariable):
            command += f'marcos.get("{child.value}").toString() + '
            macros.append(child.value)
        else:
            raise ValueError(f"could not match macro {child}")
    walker.output = f"dispatcher.execute(dispatcher.parse({command[:-3]}, source));"
    walker.macros = macros
    walker.reqiures_macros = True
    walker.reqiures_dispatcher = True

def say(walker: Walker):
    template = """
        PlayerChatMessage chatMessage;
        if (source.isPlayer())
            chatMessage = PlayerChatMessage.unsigned(Objects.requireNonNull(source.getPlayer()).getUUID(), "{text}");
        else
            chatMessage = PlayerChatMessage.system("{text}");
        PlayerList playerList = source.getServer().getPlayerList();
        playerList.broadcastChatMessage(chatMessage, source, ChatType.bind(ChatType.SAY_COMMAND, source));
    """
    def message(node: mecha.AstMessage):
        walker.output = template.format(text=node.fragments[0].value)
    walker.next(message=message)

def tp(walker: Walker):
    end = ""
    def location(node: mecha.AstVector3):
        value = vec3("source.getAnchor().apply(source)", "source.getRotation()", node)  
        walker.output += f"source.getEntityOrException().setPos({value});\n"
        walker.next(facing=lambda: facing(walker))
    def targets(node: mecha.AstNode):
        nonlocal end
        value = selector(node, walker, False)
        walker.output += f"""
            for (entity in {value}) {{
                source = source.withEntity(entity);
            """
        end += "}"
        walker.next(location=location, destination=destination)
    def destination(node: mecha.AstNode):
        walker.output += f"source.getEntityOrException().setPos({selector(node, walker, single=True)}.position());\n"
    walker.next(location=location, targets=targets)
    walker.output += end
    
def kill(walker: Walker):
    has_targets = False
    def targets(node: mecha.AstNode):
        nonlocal has_targets
        has_targets = True
        value = selector(node, walker, False)
        walker.output += f"""
            for (entity in {value}) {{
                entity.kill();
            }}
        """
    walker.next(targets=targets)
    if not has_targets:
        walker.output += "source.getEntityOrException().kill();"
    
def give(walker: Walker):
    count_ = 1
    stack = None
    def targets(node: mecha.AstNode):
        walker.output += f"for (player in {selector(node, walker, single=False, player=True)}) {{\n"
    def item(node: mecha.AstItemStack):
        nonlocal stack
        stack = item_stack(node, walker, count="%i")
    def count(node: mecha.AstNumber):
        nonlocal count_
        count_ = node.value
    walker.next(targets=targets)
    walker.next(item=item)
    walker.next(count=count)
    walker.output += f"player.getInventory().add({stack %count_});\n}}"
        
def function(walker: Walker):
    call: str = None
    macros = "new CompoundTag()"
    def name(node: mecha.AstResourceLocation):
        nonlocal call
        call = run_function(node, walker, macros="{0}")
        walker.next(**{"with": with_, "arguments": arguments})
    def with_():
        nonlocal macros
        macros = access_data(walker)
        def path(node: mecha.AstNbtPath):
            nonlocal macros
            macros = "(CompoundTag) " + nbt_path(macros, node, walker, single=True)
        walker.next(path=path)
    def arguments(node: mecha.AstNbtCompound):
        nonlocal macros
        macros = nbt(node, walker)
    walker.next(name=name)
    walker.output += call.format(macros)
    walker.reqiures_dispatcher = True

def execute(walker: Walker):
    end = "" 
    def fork(entities: str, statement = "source = source.withEntity(entity);") -> str:
        nonlocal end
        end = "});\n" + end
        return f"{entities}.forEach(entity -> {{\n{statement}\n"
    def optional(entity: str) -> str:
        nonlocal end
        end = "}\n" + end
        return f"""
            source = source.withEntity({entity}.orElse(null));
            if (source.getEntity() != null) {{
            """
    # ------------
    def subcommand(cmd: mecha.AstCommand):
        statement, _, subwalker = compile(
            cmd, 
            walker.parser, 
            walker.depots, 
            walker.functions
        )
        if subwalker.returns == True or subwalker.returns == Maybe: 
            subwalker.returns = Maybe
            if walker.returns == True:
                walker.output += statement.replace("return ", "return new MaybeReturn(true, ", 1).replace(";", ");", 1)
        else:
            walker.output += statement
        walker.reqiures_dispatcher = subwalker.reqiures_dispatcher
        walker.reqiures_macros = subwalker.reqiures_macros
        return True
    def align():
        swizzle: str = walker.next(axes=lambda node: node.value)
        coords = {
            "x": "source.getAnchor().apply(source).x",
            "y": "source.getAnchor().apply(source).y",
            "z": "source.getAnchor().apply(source).z",
        }
        for char in swizzle:
            coords[char] = f"(int) {coords[char]}"
        walker.output += f"source = source.withPosition(new Vec3({coords['x']}, {coords['y']}, {coords['z']}));\n"
    def anchored():
        anchor = walker.next(anchor=entity_anchor)
        walker.output += f"source = source.withAnchor({anchor});\n"
    def as_():
        walker.output += fork(walker.next(targets=lambda node: selector(node, walker, single=False)))
    def at():
        walker.output += fork(
            walker.next(targets=lambda node: selector(node, walker, single=False)), 
            """source = source
                    .withPosition(entity.position())
                    .withRotation(entity.getRotationVector())
                    .withLevel(entity.getServer().getLevel(entity.level().dimension()));\n"""
        )
    def in_():
        location = walker.next(dimension=lambda node: resource_location(node, walker))
        walker.output += f"source = source.withLevel(source.getServer().getLevel(ResourceKey.create(Registries.DIMENSION, {location})));\n"
    def on():
        walker.output += walker.next(
            attacker=lambda: optional("(source.getEntityOrException() instanceof Attackable e ? Optional.ofNullable(e.getLastAttacker()) : Optional.empty())"),
            controller=lambda: "source = source.withEntity(source.getEntityOrException().getControllingPassenger());\n",
            leasher=lambda: optional("(source.getEntityOrException() instanceof Leashable e ? Optional.ofNullable(e.getLeashHolder()) : Optional.empty())"),
            origin=lambda: optional("(source.getEntityOrException() instanceof TraceableEntity e ? Optional.ofNullable(e.getOwner()) : Optional.empty())"),
            owner=lambda: optional("(source.getEntityOrException() instanceof OwnableEntity e ? Optional.ofNullable(e.getOwner()) : Optional.empty())"),
            passengers=lambda: fork("source.getEntityOrException().getPassengers()"),
            target=lambda: optional("(source.getEntityOrException() instanceof Targeting e ? Optional.ofNullable(e.getTarget()) : Optional.empty())"),
            vehicle=lambda: "source = source.withEntity(source.getEntityOrException().getVehicle());\n",
        )
    def positioned():
        def pos(node: mecha.AstVector3):
            walker.output += f"source = source.withPosition({vec3('source.getAnchor().apply(source)', 'source.getRotation()', node)}).withAnchor(EntityAnchorArgument.Anchor.FEET);\n"
        def as_():
            entities = walker.next(targets=lambda node: selector(node, walker, single=False))
            walker.output += fork(entities, "source = source.withPosition(entity.position());\n")
        def over():
            map = walker.next(heightmap=heightmap)
            walker.output += f"source = source.withPosition(Vec3.atCenterOf(source.getLevel().getHeightmapPos({map}, new BlockPos(toVec3i(source.getPosition())))));\n"
        walker.next(pos=pos, over=over, **{"as": as_})
    def rotated():
        def pos(node: mecha.AstVector2):
            walker.output += f"source = source.withRotation({vec2('source.getRotation()', node)});\n"
        def as_():
            entities = walker.next(targets=lambda node: selector(node, walker, single=False))
            walker.output += fork(entities, "source = source.withRotation(entity.getRotationVector());\n")
        walker.next(pos=pos, **{"as": as_})
    def summon():
        type = walker.next(entity=lambda node: walker.parser.serialize(node))
        walker.output += f"""
            CompoundTag tag_tmp = new CompoundTag();
            tag_tmp.putString("id", "{type}");
            source = source.withEntity(Objects.requireNonNull(BuiltInRegistries.ENTITY_TYPE.get(ResourceLocation.withDefaultNamespace("")).loadEntityRecursive(tag_tmp, source.getLevel(), entity -> {{
                entity.setPos(source.getPosition());
                if (entity instanceof Mob) // randomize data ._.
                    entity.finalizeSpawn(source.getLevel(), source.getLevel().getCurrentDifficultyAt(entity.blockPosition()), MobSpawnType.COMMAND, null);
                return entity;
            }})));
        """
    def if_(is_if: bool):
        condition = ""
        def biome():
            nonlocal condition
            pos = walker.next(pos=lambda node: vec3(node, vec3i=True))
            res = walker.next(biome=lambda node: (node.is_tag, resource_location(node, walker)))
            if res[0]:
                res = f"TagKey.create(Registries.BIOME, {res[1]})"
            else:
                res = res[1]
            walker.output += f"var blockpos = new BlockPos({pos});\n"
            condition += f"source.getLevel().isLoaded(blockpos) && source.getLevel().getBiome(blockpos).is({res})"
            return "result = 1;\n"
        def block():
            nonlocal condition
            pos = f"new BlockPos({walker.next(pos=lambda node: vec3(node, vec3i=True))})"
            condition += "source.getLevel().isLoaded(blockpos) && " \
                + walker.next(block=lambda node: block_predicate(node, walker)) \
                + f".matches(source.getLevel(), {pos})"
            return "result = 1;\n"
        def blocks():
            nonlocal condition
            condition += "((Supplier<Boolean>) () -> {\n"
            start = walker.next(start=lambda node: vec3(node, vec3i=True))
            end = walker.next(end=lambda node: vec3(node, vec3i=True))
            destination = walker.next(destination=lambda node: vec3(node, vec3i=True))
            if is_if: walker.output += "int totalBlocks = 0;"
            condition += f"""
                var original = BoundingBox.fromCorners({start}, {end});
                Vec3i destenation = {destination};
                Vec3i length = original.getLength();
                var compare = BoundingBox.fromCorners(destenation, destenation.offset(original.getLength()));
                
                for (int x = 0; x <= length.getX(); x++)
                    for (int y = 0; y <= length.getY(); y++)
                        for (int z = 0; z <= length.getZ(); z++) {{
                            var original_pos = new BlockPos(x + original.minX(), y + original.minY(), z + original.minZ());
                            var compare_pos = new BlockPos(x + compare.minX(), y + compare.minY(), z + compare.minZ());
                            if (!source.getLevel().isLoaded(original_pos) || !source.getLevel().isLoaded(compare_pos)) return false;
                            var original_state = source.getLevel().getBlockState(original_pos);
            """
            condition += walker.next(all=lambda: "", masked=lambda: "if (original_state.isAir()) continue;\n")
            condition += """
                            var compare_state = source.getLevel().getBlockState(compare_pos);
                            if (original_state != compare_state) return false; //sus
                            var original_entity = source.getLevel().getBlockEntity(original_pos);
                            if (original_entity == null) continue;
                            var compare_entity = source.getLevel().getBlockEntity(compare_pos);
                            if (compare_entity == null) return false;
                            if (!original_entity.components().equals(compare_entity.components())) return false;
                            %s
                        }
                    return true;
                }).get()
            """ % "totalBlocks++;" if is_if else ""
            if is_if:
                return "result = totalBlocks;\n"
            else:
                return "result = 1;\n"
        def data():
            nonlocal condition
            walker.output += """
                boolean exists;
                int totalMatches;
                try {
                    var tags = %s;
                    exists = tags.size() > 0;
                    totalMatches = tags.size();
                } catch (NullPointerException | IndexOutOfBoundsException e) {
                    exists = false;
                }
            """ % nbt_path(access_data(walker), walker.next(path=lambda node: node), walker, single=False)
            condition += "exists"
            if is_if:
                return "result = totalMatches;\n"
            else:
                return "result = 1;\n"
        def dimension():
            nonlocal condition
            condition += "source.getLevel() == source.getServer().getLevel(ResourceKey.create(Registries.DIMENSION, %s))" \
                % resource_location(walker.next(dimension=lambda node: node), walker)
            return "result = 1;\n"
        def entity():
            nonlocal condition
            walker.output += "int matches = %s.size();\n" % selector(walker.next(entities=lambda node: node), walker, single=False)
            condition += "matches > 0" 
            if is_if:
                return "result = matches;\n"
            else:
                return "result = 1;\n"
        def function():
            nonlocal condition
            
        out = walker.next(
            biome=biome,
            block=block,
            blocks=blocks,
            data=data,
            dimension=dimension,
        )
        walker.output += f"if ({'' if is_if else '!'}({condition})) {{\n"
        nonlocal end
        end = "}\n" + end
        return out
    out = walker.next(**{
        "subcommand": subcommand,
        "align": align,
        "anchored": anchored,
        "as": as_,
        "at": at,
        "facing": lambda: facing(walker),
        "in": in_,
        "on": on,
        "positioned": positioned,
        "rotated": rotated,
        "summon": summon,
        "if": lambda: if_(True),
        "unless": lambda: if_(False),
        "run": lambda: None,
    })
    if out != True:
        exists = walker.next(subcommand=subcommand)
        if exists is None:
            if out is None:
                raise NotImplementedError("'out' is 'None' despite there being no following subcommand")
            walker.output += out
    walker.output += end
