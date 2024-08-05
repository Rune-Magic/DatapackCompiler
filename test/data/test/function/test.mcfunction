execute align xy run say something funny
execute anchored eyes run say something funny
execute as @e[type=creeper] run say something funny
execute at @p run say something funny
execute facing entity @e[type=enderman] feet run say something funny
execute in minecraft:the_nether run say something funny
execute on vehicle run say something funny
execute positioned over world_surface run say something funny
execute rotated 90 0 run say something funny
execute store result score @p funny_count run say something funny
execute store success block 0 64 0 RecordItem int 1000 run say something funny
execute store result bossbar minecraft:example max run say something funny
execute store success entity @s[type=zombie] Health int 1000 run say something funny
execute store result score @p funny_count run say something funny
execute store success storage minecraft:example data double 1 run say something funny
execute summon minecraft:sheep run say something funny
execute if block 0 64 0 minecraft:grass_block[snowy=true] run say something funny
execute unless biome 100 64 100 minecraft:desert run say something funny
execute if blocks 0 64 0 10 64 10 20 64 20 all run say something funny
execute if data block 0 64 0 Items[{id:"minecraft:diamond"}] run say something funny
execute if data entity @p Inventory[{id:"minecraft:diamond"}] run say something funny
execute if data storage minecraft:example Items[{id:"minecraft:diamond"}] run say something funny
execute in minecraft:the_end run say something funny
execute if entity @e[type=cow] run say something funny
execute if function minecraft:example run say something funny
execute if block 0 64 0 grass_block run say something funny
execute if entity @p run say something funny
execute if loaded 0 64 0 run say something funny
execute if predicate minecraft:example run say something funny
execute if score @p funny_count < @r random_count run say something funny
execute if score @p funny_count matches 1..10 run say something funny
execute run say something funny

function test:test with block ^4 ^1 ^10 foo[-1].bar[][{baz:1b}]
function test:test with block ^4 ^1 ^10 foobar{baz:true}
function test:test {nothing: "lies"}

give @s acacia_boat 1 
give @s diamond_axe[max_stack_size=16]

tp ~ 10 ~
tp ^ ^ ^
tp 0.0 0.0 0.0
tp @s ~ ~ ~ facing ~ ~10 ~
tp @s ~ ~ ~ facing entity @p eyes

data merge storage test:test {"double": 12.69, "short": 1s,"int": 1, "byte": 1b, "long": 1L, "float": 1f, "int_array": [1, 2, 3], "byte_array": [1b, 2b, 3b], "long_array": [1L, 2L, 3L], "string": "howdy", "list": [{"something": false}, {"more": ":3"}]}

kill @e[x=0,y=64,z=0,distance=..100,dx=10,dy=5,dz=10,x_rotation=-45..45,y_rotation=-90..90,scores={objective1=10..20},tag=exampleTag,team=exampleTeam,level=5..50,gamemode=survival,name=exampleName,type=minecraft:zombie,nbt={OnGround:true},advancements={story/root=true}]

say something more
$say $(nothing)
$data merge entity $(name) {CustomName:$(new)}

tp @p 100 64 100
tp @e[type=zombie] @s
tp @a @r
tp Player ~ ~ ~
tp dd12be42-52a9-4a91-a8a1-11c01849e498 ^ ^ ^

# give @p minecraft:diamond 1
# give @a minecraft:apple 5
# give @r minecraft:iron_sword

# effect give @p minecraft:speed 30 1
# effect clear @a
# effect give @e[type=sheep] minecraft:regeneration 60 1

# summon minecraft:zombie ~ ~ ~
# summon minecraft:lightning_bolt ~ ~1 ~
# summon minecraft:chicken 100 64 100

# gamemode creative @a
# gamemode survival @p
# gamemode adventure @r

# setblock 100 64 100 minecraft:stone
# setblock ~ ~1 ~ minecraft:redstone_block
# setblock ~1 ~ ~ minecraft:air

# fill 100 64 100 110 64 110 minecraft:glass
# fill ~1 ~ ~ ~10 ~10 ~10 minecraft:stone
# fill 100 64 100 110 64 110 minecraft:air

# scoreboard objectives add Health health
# scoreboard players set @p Health 20
# scoreboard players add @a[team=Red] Points 10

# title @a title {"text":"Welcome to the Server","color":"gold"}
# title @p subtitle {"text":"Good Luck!","color":"green"}
# title @r actionbar {"text":"You found a secret!","color":"red"}

# weather clear
# weather rain
# weather thunder

# time set day
# time add 1000
# time set midnight

# # Existing commands (not repeating them)

# # advancement command - grant or revoke advancements
# advancement grant @p only minecraft:story/mine_stone
# advancement revoke @a everything
# advancement grant @r from minecraft:adventure/root

# # clear command - clear items from inventory
# clear @p minecraft:diamond_sword 1
# clear @a minecraft:apple
# clear @e[type=player] minecraft:iron_ingot 0

# # clone command - copy blocks from one region to another
# clone 0 64 0 10 64 10 20 64 20
# clone 0 64 0 10 64 10 20 64 20 masked move
# clone 0 64 0 10 64 10 20 64 20 replace

# # data command - modify NBT data of entities or block entities
# data merge block 0 64 0 {Lock:"Secret"}
# data get entity @p Inventory[0]
# data remove entity @e[type=zombie, limit=1] Brain

# # defaultgamemode command - set the default game mode
# defaultgamemode survival
# defaultgamemode creative
# defaultgamemode adventure

# # difficulty command - set the difficulty level
# difficulty peaceful
# difficulty easy
# difficulty normal
# difficulty hard

# # enchant command - enchant items in a player's inventory
# enchant @p minecraft:sharpness 5
# enchant @a minecraft:unbreaking 3
# enchant @r minecraft:fortune

# # execute command - execute another command
# execute at @p run summon minecraft:lightning_bolt ~ ~ ~
# execute as @a run say Hello World
# execute if block 0 64 0 minecraft:stone run setblock 0 64 0 minecraft:diamond_block

# # experience command - add or set experience points or levels
# experience add @p 10 points
# experience set @a 5 levels
# experience add @r 1000 points

# # function command - run a function
# function mynamespace:subfolder/myfunction
# function mynamespace:another_function

# # kill command - kill entities
# kill @e[type=zombie]
# kill @p
# kill @a

# # locate command - locate structures
# locate biome minecraft:desert
# locate structure minecraft:village
# locate poi minecraft:nether_portal

# # me command - display a message about the player
# me is now ready to play!
# me found a secret cave!
# me completed the challenge!

# # msg command - send a private message to a player
# msg @p Hello there!
# msg @a Welcome to the server!
# msg @r Good luck!

# # particle command - create particles
# particle minecraft:heart ~ ~1 ~ 0 0 0 1 10
# particle minecraft:smoke ~ ~ ~ 0.5 0.5 0.5 0.1 100
# particle minecraft:flame ~ ~1 ~ 1 0 0 0.1 50 force @a

# # playsound command - play a sound
# playsound minecraft:entity.lightning_bolt.thunder master @a ~ ~ ~ 1 1 0
# playsound minecraft:ui.button.click ambient @r

# # say command - display a message to players
# say Welcome to the server!
# say Good job, everyone!
# say The game is starting now!

# # setworldspawn command - set the world spawn point
# setworldspawn 0 64 0
# setworldspawn ~ ~ ~
# setworldspawn 100 70 -100

# # spawnpoint command - set the spawn point for a player
# spawnpoint @p 0 64 0
# spawnpoint @a 100 70 100
# spawnpoint @r ~ ~ ~

# # spreadplayers command - teleport entities to random locations
# spreadplayers 0 0 10 20 false @a
# spreadplayers 100 64 10 20 true @e[type=cow]
# spreadplayers ~ ~ 5 10 false @p

# # stopsound command - stop sounds
# stopsound @a master minecraft:music.game
# stopsound @p ambient
# stopsound @r weather

# # tag command - manage entity tags
# tag @p add FoundSecret
# tag @a remove FoundSecret
# tag @r list

# # team command - manage teams
# team add RedTeam
# team remove BlueTeam
# team join RedTeam @p

# # teleport command - teleport entities (alternative to tp)
# teleport @p 200 70 200
# teleport @e[type=skeleton] @p
# teleport @a @e[type=villager, limit=1]

# # weather command - change weather (added a variant usage)
# weather clear 100000

# # time command - change time (added a variant usage)
# time query daytime
# time query gametime

