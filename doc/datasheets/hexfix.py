import json, csv

# Get the damn files
with open('sitara_termmodes.json') as jsonfile:
    termmodes = json.load(jsonfile)

# Carry on then
for key in termmodes:
    try:
        # Get the old shit
        oldvalue = int(termmodes[key]['control_reg_offset'], 16)
        # Subtract out the pesky bit at the beginning
        newvalue = oldvalue - 2048
        # Make a string out of it
        newstr = hex(newvalue)
        # Cleverly make sure it's a specific length
        fill = (5 - len(newstr)) * '0'
        pre, post = newstr.split('x', 1)
        newstr = pre + 'x' + fill + post
        termmodes[key]['control_reg_offset'] = newstr
    except KeyError:
        pass

with open('sitara_termmodes.json', 'w+') as jsonfile:
    json.dump(termmodes, jsonfile, indent=4)