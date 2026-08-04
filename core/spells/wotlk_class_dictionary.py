# Maps a BASE ability name (the thing a card explicitly says it borrows
# modifiers from) to its real WotLK 3.3.5 owning class. This is standard
# WoW knowledge about the *base* spell, not a guess about the Ascension
# card that borrows from it - the card's own name/school can differ
# entirely from its tag (primer §4, the whole point of the class-tag rule).
BASE_ABILITY_CLASS = {
    # Warrior
    'Bladestorm':'Warrior','Bloodthirst':'Warrior','Charge':'Warrior','Cleave':'Warrior',
    "Colossus Smash":'Warrior','Concussion Blow':'Warrior','Devastate':'Warrior','Execute':'Warrior',
    'Heroic Strike':'Warrior','Mortal Strike':'Warrior','Overpower':'Warrior','Rend':'Warrior',
    'Revenge':'Warrior','Shield Slam':'Warrior','Shockwave':'Warrior','Slam':'Warrior',
    'Sundering':'Warrior','Thunder Clap':'Warrior','Whirlwind':'Warrior','Intercept':'Warrior',
    'Intervene':'Warrior','Raging Blow':'Warrior','Siegebreaker':'Warrior',
    # Paladin
    'Consecration':'Paladin','Crusader Strike':'Paladin','Exorcism':'Paladin',
    'Hammer of Justice':'Paladin','Holy Light':'Paladin','Holy Wrath':'Paladin',
    'Seal of Vengeance':'Paladin',
    # Priest
    'Devouring Plague':'Priest','Holy Nova':'Priest','Pain Suppression':'Priest',
    'Penance':'Priest','Penance heal':'Priest','Prayer of Healing':'Priest',
    'Psychic Scream':'Priest','Renew':'Priest','Vampiric Touch':'Priest','Halo':'Priest',
    'Smite':'Priest',
    # Druid
    'Cat Form':'Druid','Claw':'Druid','Entangling Roots':'Druid','Ferocious Bite':'Druid',
    'Force of Nature':'Druid','Hurricane':'Druid','Insect Swarm':'Druid','Mangle':'Druid',
    'Maul':'Druid','Moonfire':'Druid','Rake':'Druid','Rip':'Druid','Shred':'Druid',
    'Starfall':'Druid','Starfire':'Druid','Starsurge':'Druid','Swipe':'Druid','Wrath':'Druid',
    "Tiger's Fury":'Druid',
    # Rogue
    'Backstab':'Rogue','Eviscerate':'Rogue','Fan of Knives':'Rogue','Hemorrhage':'Rogue',
    'Mutilate':'Rogue','Pick Pocket':'Rogue','Riposte':'Rogue','Rupture':'Rogue',
    'Shadowstep':'Rogue','Sinister Strike':'Rogue','Vanish':'Rogue','Killing Spree':'Rogue',
    'Slice and Dice':'Rogue',
    # Hunter
    'Aimed Shot':'Hunter','Arcane Shot':'Hunter','Black Arrow':'Hunter','Explosive Shot':'Hunter',
    'Glaive Toss':'Hunter','Kill Shot':'Hunter','Mongoose Bite':'Hunter','Multi-Shot':'Hunter',
    'Raptor Strike':'Hunter','Serpent Sting':'Hunter','Steady Shot':'Hunter','Counterattack':'Hunter',
    # Mage
    'Arcane Barrage':'Mage','Arcane Blast':'Mage','Arcane Explosion':'Mage','Arcane Missiles':'Mage',
    'Blast Wave':'Mage','Blink':'Mage','Cone of Cold':'Mage',"Dragon's Breath":'Mage',
    'Fireball':'Mage','Flamestrike':'Mage','Frost Nova':'Mage','Frostbolt':'Mage',
    'Pyroblast':'Mage','Scorch':'Mage','Slow':'Mage',
    # Warlock
    'Corruption':'Warlock','Curse of Exhaustion':'Warlock','Curse of the Elements':'Warlock',
    'Drain Life':'Warlock','Fel Domination':'Warlock','Haunt':'Warlock','Immolate':'Warlock',
    'Incinerate':'Warlock','Rain of Fire':'Warlock','Searing Pain':'Warlock',
    'Seed of Corruption':'Warlock','Shadow Bolt':'Warlock','Shadowburn':'Warlock','Fear':'Warlock',
    # Shaman
    'Chain Heal':'Shaman','Chain Lightning':'Shaman','Earth Shock':'Shaman',
    'Fire Elemental Totem':'Shaman','Flame Shock':'Shaman','Frost Shock':'Shaman',
    'Lava Burst':'Shaman','Lava Lash':'Shaman','Lightning Shield':'Shaman',
    'Searing Totem':'Shaman','Stormstrike':'Shaman','Thunderstorm':'Shaman',
    'Feral Spirits':'Shaman',
    # Death Knight
    'Blood Strike':'Death Knight','Death Strike':'Death Knight','Obliterate':'Death Knight',
}

# Known non-class flavor text that matches the "uses X modifiers" regex but
# is NOT a real class-tag reference (jokes / meme cards) - exclude explicitly.
NOT_A_CLASS_REFERENCE = {'crate'}
