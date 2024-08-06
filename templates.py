function_template = """
    case "{function}":
        {body}
        return 0;
"""

entry_point_template = """
package datapack.{name};

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.datafixers.util.Pair;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.advancements.critereon.*;
import net.minecraft.commands.*;
import net.minecraft.commands.arguments.*;
import net.minecraft.commands.arguments.selector.EntitySelector;
import net.minecraft.core.*;
import net.minecraft.core.component.*;
import net.minecraft.core.registries.*;
import net.minecraft.nbt.*;
import net.minecraft.network.chat.*;
import net.minecraft.resources.*;
import net.minecraft.server.RegistryLayer;
import net.minecraft.server.commands.data.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.players.PlayerList;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.*;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.phys.*;
import org.slf4j.*;

import java.util.*;
import java.util.function.*;
import java.util.stream.Collectors;

public class EntryPoint implements ModInitializer {{
    public static List<String> COMPILED = List.of(
        {to_compile}    
    );
    
    public static String MODID = "{name}";
    public static final Logger LOGGER = LoggerFactory.getLogger(MODID);

	{depots}

    @Override
    public void onInitialize() {{
        LOGGER.info("Initilizing {name}");
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {{
            dispatcher.register(Commands.literal("_function__{name}")
                    .requires(ctx -> ctx.hasPermission(2))
                    .then(Commands.argument("id", StringArgumentType.word()).then(Commands.argument("macros", CompoundTagArgument.compoundTag()).executes(
                            ctx -> function(ctx.getSource(), StringArgumentType.getString(ctx, "id"), CompoundTagArgument.getCompoundTag(ctx, "macros"), dispatcher)
                    ))));
        }});
    }}
    
    private enum Sort implements BiConsumer<Vec3, List<? extends Entity>> {{
        NEAREST("nearest", (pos, pair) -> pair.getFirst().position().distanceToSqr(pos) > pair.getSecond().position().distanceToSqr(pos)),
        FURTHEST("furthest", (pos, pair) -> pair.getFirst().position().distanceToSqr(pos) < pair.getSecond().position().distanceToSqr(pos)),
        ARBITRARY("arbitrary", (pos, pair) -> false),
        RANDOM("random", null);
        
        final String id;
        final BiPredicate<Vec3, Pair<Entity, Entity>> predicate;
        
        Sort(String id, BiPredicate<Vec3, Pair<Entity, Entity>> predicate) {{
            this.id = id;
            this.predicate = predicate;
        }}
    
        @Override
        public void accept(Vec3 vec3, List<? extends Entity> entities) {{
            if (predicate == null) {{
                Collections.shuffle(entities);
                return;
            }}
            
            List<Entity> modifiableEntities = new ArrayList<>(entities);
            while (true) {{
                boolean okay = true;
                Entity last = null;
                int i = 0;
                for (Entity entity : modifiableEntities) {{
                    if (last != null && predicate.test(vec3, Pair.of(last, entity))) {{
                        modifiableEntities.set(i, last);
                        modifiableEntities.set(i - 1, entity);
                        if (okay) okay = false;
                    }}
                    last = entity;
                    i++;
                }}
                if (okay) {{
                    for (int j = 0; j < entities.size(); j++) {{
                        ((List<Entity>) entities).set(j, modifiableEntities.get(j));
                    }}
                    return;
                }}
            }}
        }}
    }}

    private static boolean nbtMatches(CompoundTag original, CompoundTag with) {{
        for (key in original.getAllKeys()) {{
            if (!with.contains(key)) continue;
            TagType<? extends Tag> o = original.get(key).getType();
            TagType<? extends Tag> w = with.get(key).getType();
            if (o != w) return false;
            var item = original.get(key);
            if (item instanceof CollectionTag<? extends Tag>) {{
                if (!nbtMatches(item, ((CollectionTag<? extends Tag>)with.get(key))))
                    return false;
            }} else if (o == CompoundTag.TYPE) {{
                if (!nbtMatches(original.getCompound(key), with.getCompound(key)))
                    return false;
            }} else {{
                if (!original.get(key).equals(with.get(key)))
                    return false;
            }}
        }}
        return true;
    }}
    private static boolean nbtMatches(CollectionTag<?> original, CollectionTag<?> with) {{
        int i = 0;
        for (tag in with) {{
            if (!original.contains(tag)) return false; //TODO: confirm
            i++;
        }}
        return true;
    }}

    private static Vec2 rotationFromDirection(Vec3 vec) {{
        float pitch = (float) Math.asin(vec.y);
        float h = (float) Math.sqrt(vec.x * vec.x + vec.z * vec.z);

        float yaw = (float) -Math.atan2(vec.x, vec.z) - (float) Math.PI;

        return new Vec2(pitch * (180F / (float) Math.PI), yaw * (180F / (float) Math.PI));
    }}

    private static Vec3i toVec3i(Vec3 vec3) {{
        return new Vec3i((int) vec3.x(), (int) vec3.y(), (int) vec3.z());
    }}

    private static CompoundTag returnIfMatches(Tag value, CompoundTag with) {{
        if (value instanceof CompoundTag)
            return nbtMatches(value, with) ? value : new CompoundTag();
        return new CompoundTag();
    }}

    private record MaybeReturn(boolean maybe, int value) {{
        Object out() {{
            if (maybe)
                return (Integer) value;
            return null;
        }}
    }}
    
    class Termination extends Exception {{ }}
    
    private static int function(CommandSourceStack source, String id, CompoundTag marcos, CommandDispatcher<CommandSourceStack> dispatcher) throws CommandSyntaxException {{
		switch (id) {{
			{commands}
			default:
				source.sendFailure(Component.literal("unable to find: " + id));
                return -1;
		}}
	}}
}}
"""

mod_config_template = """
{{
	"schemaVersion": 1,
	"id": "{name}",
	"version": "{version}",
	"name": "{title}",
	"description": "{desc}",
	"authors": [
		"Auto generated", "{author}"
	],
	"contact": {{
		"homepage": "https://gitlab.com/infinit-empires",
		"sources": "https://gitlab.com/infinit-empires/compiler"
	}},
	"license": "CC0-1.0",
	"icon": "assets/template-mod/icon.png",
	"environment": "server",
	"entrypoints": {{
		"main": [
			"datapack.{name}.EntryPoint"
		]
	}},
	"mixins": [
	],
	"depends": {{
		"fabricloader": ">=0.15.11",
		"minecraft": "~1.21",
		"java": ">=21",
		"fabric-api": "*"
	}}
}}
"""
